from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .forms import PaymentRequestForm
from .models import Conversation, Message, can_chat, can_chat_together, open_payment_for_upload


class ChatConsumer(JsonWebsocketConsumer):
    """One WebSocket per open chat page. Both participants of a conversation
    join the same group, so a message sent by one reaches the other at once."""

    def connect(self):
        user = self.scope['user']
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']

        # Only the two people in the conversation may listen to it, and only while
        # both may still chat (see can_chat in models.py).
        conversation = self.get_conversation() if can_chat(user) else None
        if conversation is None:
            self.close()
            return

        self.group_name = f'chat_{conversation.pk}'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    # Papildinājums, la pieņem arī citu message lauku tipus - maksājumiem un attēliem
    def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            return

        # Checked again for every message: the conversation may have been deleted,
        # or one side may have become an admin, since the socket opened.
        conversation = self.get_conversation()

        if conversation is None:
            self.close()
            return

        user = self.scope['user']
        action = content.get('action')

        # Parasta teksta ziņa
        if action == 'message':
            text = content.get('message', '').strip()[:Message.MAX_LENGTH]

            if not text:
                return

            message = Message.objects.create(
                conversation=conversation,
                sender=user,
                text=text
            )

        # Maksājuma pieprasījums
        elif action == 'payment':
            if not user.is_photographer:
                return

            # The latest request is paid and its images are not uploaded yet:
            # no new request before that, or the paid one could never be used.
            if open_payment_for_upload(conversation) is not None:
                self.send_error('Vispirms pievieno attēlus par apmaksāto pieprasījumu.')
                return

            form = PaymentRequestForm(content)
            if not form.is_valid():
                # Tell the sender why the request was refused
                self.send_error(' '.join(e for errors in form.errors.values() for e in errors))
                return

            # A new request cancels the older ones that still wait for payment.
            for old in Message.objects.filter(conversation=conversation, message_type='payment',
                                              payment_status='pending'):
                self.change_payment_status(old, 'cancelled')

            message = Message.objects.create(
                conversation=conversation,
                sender=user,
                text='Maksājuma pieprasījums',
                message_type='payment',
                payment_amount=form.cleaned_data['amount'],
                currency=form.cleaned_data['currency'],
                payment_status='pending'
            )

        # Maksājuma apstiprināšana (demonstrācija)
        elif action == 'pay':
            if user.pk != conversation.client_id:
                return

            payment_id = content.get('payment_id')

            if not str(payment_id).isdigit():
                return

            payment = Message.objects.filter(
                pk=int(payment_id),
                conversation=conversation,
                message_type='payment',
                sender=conversation.photographer
            ).first()

            if payment is None:
                return

            if not self.change_payment_status(payment, 'paid'):
                self.send_error('Šis pieprasījums vairs nav spēkā (tas ir atcelts vai jau apmaksāts).')
                return

            Conversation.objects.filter(pk=conversation.pk).update(
                updated_at=payment.created_at
            )
            return

        # The photographer cancels a request that is not paid yet
        elif action == 'cancel_payment':
            if not user.is_photographer:
                return

            payment_id = content.get('payment_id')

            if not str(payment_id).isdigit():
                return

            payment = Message.objects.filter(
                pk=int(payment_id),
                conversation=conversation,
                message_type='payment',
                sender=user
            ).first()

            if payment is None:
                return

            if not self.change_payment_status(payment, 'cancelled'):
                self.send_error('Šo pieprasījumu vairs nevar atcelt (tas ir apmaksāts vai jau atcelts).')
            return

        else:
            return

        Conversation.objects.filter(pk=conversation.pk).update(
            updated_at=message.created_at
        )

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'chat.message',
                'message': message.to_json()
            }
        )

    def send_error(self, text):
        """Tells only the sender why a request was refused."""
        self.send_json({'event': 'error', 'error': text})

    def change_payment_status(self, payment, new_status):
        """Moves a payment request that is still pending to new_status ('paid' or
        'cancelled') and tells everyone in the conversation. Only a pending request
        changes, so a payment and a cancel arriving at once cannot both succeed;
        returns False if the request was no longer pending."""
        changed = Message.objects.filter(pk=payment.pk, payment_status='pending').update(payment_status=new_status)
        if not changed:
            return False
        payment.payment_status = new_status
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {'type': 'chat.payment_update', 'message': payment.to_json()}
        )
        return True

    # Atjaunina maksājuma statusu
    def chat_payment_update(self, event):
        self.send_json({
            'event': 'payment_update',
            'message': event['message']
        })

    # Called for every 'chat.message' event sent to the group.
    def chat_message(self, event):
        self.send_json(event['message'])

    def get_conversation(self):
        """The conversation if the current user is in it and both sides may chat, else None."""
        user = self.scope['user']
        conversation = (Conversation.objects.select_related('client', 'photographer')
                        .filter(pk=self.conversation_id).first())
        if conversation is None or not conversation.has_participant(user):
            return None
        if not can_chat_together(conversation.client, conversation.photographer):
            return None
        return conversation
