import functools
import io
import os
import tempfile
import zipfile
from decimal import Decimal

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from PIL import Image

from testsite.models import User

from .consumers import ChatConsumer
from .models import Conversation, Message, MessageImage

PASSWORD = 'Drosa-parole-731'


def image_file(name='a.png', color='red', size=(40, 30), fmt='PNG'):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue())


class UploadTests(TestCase):
    """One batch of images (up to 10 files) per paid payment request, all or nothing."""

    def setUp(self):
        # Uploaded files go to a fresh temporary folder for every test.
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.photographer = User.objects.create_user('foto', 'foto@example.com', PASSWORD, role=User.PHOTOGRAPHER)
        self.client_user = User.objects.create_user('klients', 'klients@example.com', PASSWORD)
        self.conversation = Conversation.get_or_create_between(self.client_user, self.photographer)
        self.url = reverse('testsite:chat_upload_images', args=[self.conversation.pk])
        self.client.login(username='foto', password=PASSWORD)

    def payment(self, status='paid'):
        return Message.objects.create(
            conversation=self.conversation, sender=self.photographer, text='Maksājuma pieprasījums',
            message_type='payment', payment_amount=Decimal('10.00'), currency='EUR', payment_status=status)

    def upload(self, *files):
        return self.client.post(self.url, {'images': list(files)})

    def stored_files(self):
        return [name for _, _, names in os.walk(self.media.name) for name in names]

    def batches(self):
        return Message.objects.filter(message_type='image')

    def test_refused_without_a_payment_request(self):
        self.assertEqual(self.upload(image_file()).status_code, 403)
        self.assertEqual(self.batches().count(), 0)

    def test_refused_while_the_payment_is_not_paid(self):
        self.payment('pending')
        self.assertEqual(self.upload(image_file()).status_code, 403)

    def test_only_the_photographer_may_upload(self):
        self.payment()
        self.client.login(username='klients', password=PASSWORD)
        self.assertEqual(self.upload(image_file()).status_code, 404)

    def test_paid_request_allows_one_batch_with_zip_and_copies(self):
        payment = self.payment()
        files = [image_file('holiday-one.png'), image_file('holiday-two.jpg', 'blue', fmt='JPEG')]
        originals = {file.name: file.read() for file in files}
        for file in files:
            file.seek(0)
        response = self.upload(*files)
        self.assertEqual(response.status_code, 200)
        message = self.batches().get()
        self.assertEqual(message.payment_request, payment)
        self.assertEqual(MessageImage.objects.filter(message=message).count(), 2)
        data = response.json()['message']
        self.assertEqual(data['type'], 'image')
        self.assertEqual(len(data['images']), 2)
        with zipfile.ZipFile(message.archive.path) as archive:
            self.assertEqual(sorted(archive.namelist()), ['holiday-one.png', 'holiday-two.jpg'])
            for name, content in originals.items():
                self.assertEqual(archive.read(name), content)  # originals, unchanged
        for stored in self.stored_files():  # random names, not the original ones
            self.assertNotIn('holiday', stored)

    def test_second_batch_for_the_same_payment_is_refused(self):
        self.payment()
        self.assertEqual(self.upload(image_file()).status_code, 200)
        self.assertEqual(self.upload(image_file()).status_code, 403)
        self.assertEqual(self.batches().count(), 1)

    def test_a_new_paid_request_opens_the_next_batch(self):
        self.payment()
        self.upload(image_file())
        second = self.payment('pending')
        self.assertEqual(self.upload(image_file()).status_code, 403)
        second.payment_status = 'paid'
        second.save()
        self.assertEqual(self.upload(image_file()).status_code, 200)
        self.assertEqual(self.batches().count(), 2)

    def test_only_the_latest_payment_counts(self):
        self.payment('paid')
        self.payment('pending')  # newer, not paid yet: the older paid one cannot be used
        self.assertEqual(self.upload(image_file()).status_code, 403)

    def test_one_invalid_file_refuses_the_whole_batch(self):
        self.payment()
        bad = SimpleUploadedFile('notes.png', b'this is not a picture')
        response = self.upload(image_file('a.png'), bad, image_file('c.png'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('notes.png', response.json()['error'])
        self.assertEqual(self.batches().count(), 0)
        self.assertEqual(self.stored_files(), [])
        # nothing was used up: a valid upload still works
        self.assertEqual(self.upload(image_file()).status_code, 200)

    def test_gif_is_refused_even_though_it_is_an_image(self):
        self.payment()
        self.assertEqual(self.upload(image_file('a.gif', fmt='GIF')).status_code, 400)

    def test_more_than_ten_files_are_refused(self):
        self.payment()
        self.assertEqual(self.upload(*[image_file(f'{i}.png') for i in range(11)]).status_code, 400)
        self.assertEqual(self.upload(*[image_file(f'{i}.png') for i in range(10)]).status_code, 200)

    def test_file_over_10_mb_is_refused(self):
        self.payment()
        big = SimpleUploadedFile('big.png', b'x' * (10 * 1024 * 1024 + 1))
        self.assertEqual(self.upload(big).status_code, 400)

    def test_no_files_are_refused(self):
        self.payment()
        self.assertEqual(self.upload().status_code, 400)

    def test_chat_page_has_the_upload_dialog_for_the_photographer_only(self):
        page = reverse('testsite:chat_conversation', args=[self.conversation.pk])
        photographer_page = self.client.get(page).content.decode()
        self.assertIn('id="upload-dialog"', photographer_page)
        self.assertIn('id="image-btn"', photographer_page)
        self.assertIn('id="preview-dialog"', photographer_page)
        self.client.login(username='klients', password=PASSWORD)
        client_page = self.client.get(page).content.decode()
        self.assertIn('id="preview-dialog"', client_page)  # both sides can open the larger preview
        self.assertNotIn('id="upload-dialog"', client_page)
        self.assertNotIn('id="image-btn"', client_page)

    def test_history_of_a_batch_has_the_zip_and_the_images(self):
        self.payment()
        self.upload(image_file('a.png'), image_file('b.png', 'blue'))
        self.client.login(username='klients', password=PASSWORD)
        response = self.client.get(reverse('testsite:chat_messages', args=[self.conversation.pk]) + '?after=0')
        batch = [m for m in response.json()['messages'] if m['type'] == 'image'][0]
        self.assertTrue(batch['archive_url'].endswith('.zip'))
        self.assertEqual(len(batch['images']), 2)

    def test_deleting_a_batch_deletes_its_files(self):
        self.payment()
        self.upload(image_file('a.png'), image_file('b.png', 'blue'))
        self.assertEqual(len(self.stored_files()), 5)  # the zip, 2 thumbnails, 2 previews
        with self.captureOnCommitCallbacks(execute=True):
            self.batches().get().delete()
        self.assertEqual(self.stored_files(), [])

    def test_deleting_the_conversation_deletes_the_files_too(self):
        self.payment()
        self.upload(image_file())
        with self.captureOnCommitCallbacks(execute=True):
            self.conversation.delete()
        self.assertEqual(self.stored_files(), [])

    def test_same_file_names_get_different_names_in_the_zip(self):
        self.payment()
        self.upload(image_file('a.png'), image_file('a.png', 'blue'))
        with zipfile.ZipFile(self.batches().get().archive.path) as archive:
            self.assertEqual(sorted(archive.namelist()), ['a-2.png', 'a.png'])


def closes_sockets(test):
    """Disconnects the sockets a test opened when it ends, even if it fails
    (Django's test cases have no async clean-up of their own)."""
    @functools.wraps(test)
    async def wrapper(self):
        try:
            await test(self)
        finally:
            for communicator in self.communicators:
                await communicator.disconnect()
    return wrapper


class PaymentConsumerTests(TransactionTestCase):
    """The payment actions of the chat WebSocket: requesting, paying and cancelling."""

    def setUp(self):
        self.communicators = []
        self.photographer = User.objects.create_user('foto', 'foto@example.com', PASSWORD, role=User.PHOTOGRAPHER)
        self.client_user = User.objects.create_user('klients', 'klients@example.com', PASSWORD)
        self.conversation = Conversation.get_or_create_between(self.client_user, self.photographer)

    async def connect(self, user):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f'/ws/chat/{self.conversation.pk}/')
        communicator.scope['user'] = user
        communicator.scope['url_route'] = {'kwargs': {'conversation_id': self.conversation.pk}}
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.communicators.append(communicator)
        return communicator

    async def send_request(self, communicator, amount='10'):
        await communicator.send_json_to({'action': 'payment', 'amount': amount, 'currency': 'EUR'})

    @sync_to_async
    def status_of(self, message_id):
        return Message.objects.get(pk=message_id).payment_status

    @sync_to_async
    def payment_count(self):
        return Message.objects.filter(message_type='payment').count()

    @sync_to_async
    def add_batch_for(self, payment_id):
        return Message.objects.create(conversation=self.conversation, sender=self.photographer,
                                      message_type='image', payment_request_id=payment_id)

    @closes_sockets
    async def test_payment_request_starts_pending(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        self.assertEqual((message['type'], message['payment_status']), ('payment', 'pending'))

    @closes_sockets
    async def test_new_request_cancels_the_older_pending_one(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer, '10')
        first = await photographer.receive_json_from()
        await self.send_request(photographer, '20')
        update = await photographer.receive_json_from()
        second = await photographer.receive_json_from()
        self.assertEqual(update['event'], 'payment_update')
        self.assertEqual((update['message']['id'], update['message']['payment_status']), (first['id'], 'cancelled'))
        self.assertEqual((second['type'], second['payment_status']), ('payment', 'pending'))
        self.assertEqual(await self.status_of(first['id']), 'cancelled')

    @closes_sockets
    async def test_photographer_cancels_a_pending_request(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        await photographer.send_json_to({'action': 'cancel_payment', 'payment_id': message['id']})
        update = await photographer.receive_json_from()
        self.assertEqual(update['message']['payment_status'], 'cancelled')
        self.assertEqual(await self.status_of(message['id']), 'cancelled')

    @closes_sockets
    async def test_client_cannot_cancel(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        client = await self.connect(self.client_user)
        await client.send_json_to({'action': 'cancel_payment', 'payment_id': message['id']})
        self.assertTrue(await client.receive_nothing())
        self.assertEqual(await self.status_of(message['id']), 'pending')

    @closes_sockets
    async def test_only_the_client_can_pay(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        await photographer.send_json_to({'action': 'pay', 'payment_id': message['id']})
        self.assertTrue(await photographer.receive_nothing())
        self.assertEqual(await self.status_of(message['id']), 'pending')

    @closes_sockets
    async def test_paid_request_cannot_be_cancelled(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        client = await self.connect(self.client_user)
        await client.send_json_to({'action': 'pay', 'payment_id': message['id']})
        self.assertEqual((await client.receive_json_from())['message']['payment_status'], 'paid')
        await photographer.receive_json_from()  # the same update, for the photographer
        await photographer.send_json_to({'action': 'cancel_payment', 'payment_id': message['id']})
        self.assertEqual((await photographer.receive_json_from())['event'], 'error')
        self.assertEqual(await self.status_of(message['id']), 'paid')

    @closes_sockets
    async def test_cancelled_request_cannot_be_paid(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        await photographer.send_json_to({'action': 'cancel_payment', 'payment_id': message['id']})
        await photographer.receive_json_from()
        client = await self.connect(self.client_user)
        await client.send_json_to({'action': 'pay', 'payment_id': message['id']})
        self.assertEqual((await client.receive_json_from())['event'], 'error')
        self.assertEqual(await self.status_of(message['id']), 'cancelled')

    @closes_sockets
    async def test_new_request_is_refused_while_the_paid_one_has_no_batch(self):
        photographer = await self.connect(self.photographer)
        await self.send_request(photographer)
        message = await photographer.receive_json_from()
        client = await self.connect(self.client_user)
        await client.send_json_to({'action': 'pay', 'payment_id': message['id']})
        await client.receive_json_from()
        await photographer.receive_json_from()
        await self.send_request(photographer, '20')
        self.assertEqual((await photographer.receive_json_from())['event'], 'error')
        self.assertEqual(await self.payment_count(), 1)
        # once the images are uploaded, a new request is fine again
        await self.add_batch_for(message['id'])
        await self.send_request(photographer, '20')
        self.assertEqual((await photographer.receive_json_from())['type'], 'payment')
        self.assertEqual(await self.payment_count(), 2)
