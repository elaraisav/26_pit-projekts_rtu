from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .models import Conversation, Message, can_chat, can_chat_together


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

            try:
                from decimal import Decimal
                amount = Decimal(str(content.get('amount', '')))
            except (ValueError, TypeError):
                return

            currency = content.get('currency', '')

            if amount <= 0 or amount > Decimal('99999999.99'):
                return

            if currency not in ['EUR', 'USD', 'GBP']:
                return

            message = Message.objects.create(
                conversation=conversation,
                sender=user,
                text='Maksājuma pieprasījums',
                message_type='payment',
                payment_amount=amount,
                currency=currency,
                payment_status='pending'
            )

        # Maksājuma apstiprināšana (demonstrācija)
        elif action == 'pay':
            payment_id = content.get('payment_id')

            if not str(payment_id).isdigit():
                return

            payment = Message.objects.filter(
                pk=int(payment_id),
                conversation=conversation,
                message_type='payment',
                sender=conversation.photographer,
                payment_status='pending'
            ).first()

            if user.pk != conversation.client_id or payment is None:
                return

            payment.payment_status = 'paid'
            payment.save(update_fields=['payment_status'])

            Conversation.objects.filter(pk=conversation.pk).update(
                updated_at=payment.created_at
            )

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'chat.payment_update',
                    'message': payment.to_json()
                }
            )
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
