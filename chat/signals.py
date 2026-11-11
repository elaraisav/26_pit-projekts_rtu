"""Deletes the stored files of an image batch when its database rows are deleted
(in the admin, together with a conversation, ...)."""
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Message, MessageImage


def delete_after_commit(*field_files):
    """Deletes the files once the database delete is committed (not if it is rolled back)."""
    targets = [(field_file.storage, field_file.name) for field_file in field_files if field_file]

    def delete():
        for storage, name in targets:
            storage.delete(name)

    transaction.on_commit(delete)


@receiver(post_delete, sender=Message)
def delete_batch_zip(sender, instance, **kwargs):
    delete_after_commit(instance.archive)


@receiver(post_delete, sender=MessageImage)
def delete_batch_images(sender, instance, **kwargs):
    delete_after_commit(instance.thumbnail, instance.preview)
