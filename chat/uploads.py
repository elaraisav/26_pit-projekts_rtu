"""Turns one image upload (up to 10 files) into what the chat stores: a zip with the
original files, and a thumbnail and a preview of every picture.

The checks run on all files first and nothing is saved unless every file is valid;
if saving fails half way, the files already written are deleted again."""
import io
import os
import shutil
import tempfile
import zipfile
from collections import namedtuple

from django.core.files.base import ContentFile, File
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.utils.text import get_valid_filename
from PIL import Image, ImageOps

from .models import Message, MessageImage, open_payment_for_upload

MAX_FILES = 10
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_PIXELS = 50_000_000  # width x height; protects the server from huge pictures
ALLOWED_FORMATS = {'JPEG', 'PNG'}
THUMBNAIL_SIZE = (240, 240)
PREVIEW_SIZE = (1200, 1200)

NOT_OPEN = ('Attēlus var augšupielādēt tikai pēc tam, kad ir apmaksāts jaunākais maksājuma pieprasījums, '
            'un tikai vienu komplektu par katru pieprasījumu.')


class UploadError(Exception):
    """The upload was refused; the text is shown to the photographer (in Latvian)."""


# One checked file: its name, the uploaded file (for the zip), and the two small copies.
Item = namedtuple('Item', 'name uploaded thumbnail preview')


def jpeg_copy(image, size):
    copy = image.copy()
    copy.thumbnail(size)
    buffer = io.BytesIO()
    copy.save(buffer, 'JPEG', quality=85)
    return ContentFile(buffer.getvalue())


def check_file(uploaded):
    """Returns an Item, or raises ValueError if the file is not a usable JPG or PNG."""
    if uploaded.size > MAX_FILE_SIZE:
        raise ValueError('too big')
    with Image.open(uploaded) as image:
        if image.format not in ALLOWED_FORMATS or image.width * image.height > MAX_PIXELS:
            raise ValueError('not allowed')
        # Decoding the whole picture also catches damaged files. Flatten transparency on white,
        # because the copies are JPEG.
        rgba = ImageOps.exif_transpose(image).convert('RGBA')
    flat = Image.new('RGB', rgba.size, 'white')
    flat.paste(rgba, mask=rgba.getchannel('A'))
    uploaded.seek(0)
    return Item(uploaded.name, uploaded, jpeg_copy(flat, THUMBNAIL_SIZE), jpeg_copy(flat, PREVIEW_SIZE))


def process_files(files):
    """Checks every file; raises UploadError unless all are valid."""
    if not files:
        raise UploadError('Nav izvēlēts neviens attēls.')
    if len(files) > MAX_FILES:
        raise UploadError(f'Vienā komplektā var būt ne vairāk kā {MAX_FILES} attēli.')
    items, bad = [], []
    for uploaded in files:
        try:
            items.append(check_file(uploaded))
        except Exception:  # damaged, wrong type, too big, decompression bomb, ...
            bad.append(os.path.basename(uploaded.name))
    if bad:
        raise UploadError('Šie faili nav derīgi (jābūt JPG vai PNG, līdz 10 MB): ' + ', '.join(bad) + '. Nekas netika augšupielādēts.')
    return items


def write_zip(target, items):
    """Writes the original files into a zip (pictures are compressed already, so stored as they are)."""
    used = set()
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as archive:
        for index, item in enumerate(items, 1):
            name = get_valid_filename(os.path.basename(item.name)) or f'attels-{index}'
            stem, extension = os.path.splitext(name)
            candidate, number = name, 1
            while candidate.lower() in used:
                number += 1
                candidate = f'{stem}-{number}{extension}'
            used.add(candidate.lower())
            item.uploaded.seek(0)
            with archive.open(candidate, 'w') as out:
                shutil.copyfileobj(item.uploaded, out)


def create_batch(conversation, sender, items):
    """Saves the batch as one chat message, for the conversation's open payment request.
    Raises UploadError if the upload is no longer allowed (for example two uploads at once)."""
    saved = []  # names of stored files, deleted again if anything fails
    try:
        with transaction.atomic():
            payment = open_payment_for_upload(conversation)  # checked again inside the transaction
            if payment is None:
                raise UploadError(NOT_OPEN)
            message = Message(conversation=conversation, sender=sender, message_type='image',
                              payment_request=payment)
            with tempfile.TemporaryFile() as temp:
                write_zip(temp, items)
                temp.seek(0)
                message.archive.save('batch.zip', File(temp), save=False)
            saved.append(message.archive.name)
            message.save()  # the unique constraint stops a second batch for the same request
            for position, item in enumerate(items):
                image = MessageImage(message=message, position=position)
                image.thumbnail.save('thumbnail.jpg', item.thumbnail, save=False)
                saved.append(image.thumbnail.name)
                image.preview.save('preview.jpg', item.preview, save=False)
                saved.append(image.preview.name)
                image.save()
    except Exception as error:
        for name in saved:
            default_storage.delete(name)
        if isinstance(error, IntegrityError):
            raise UploadError(NOT_OPEN) from error
        raise
    return message
