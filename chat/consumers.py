from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .models import Conversation, Message


class ChatConsumer(JsonWebsocketConsumer):
    """One WebSocket per open chat page. Both participants of a conversation
    join the same group, so a message sent by one reaches the other at once."""

    def connect(self):
        user = self.scope['user']
        conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        conversation = Conversation.objects.filter(pk=conversation_id).first()

        # Only the two people in the conversation may listen to it.
        if not user.is_authenticated or conversation is None or not conversation.has_participant(user):
            self.close()
            return

        self.conversation = conversation
        self.group_name = f'chat_{conversation.pk}'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def receive_json(self, content, **kwargs):
        text = str(content.get('message', '')).strip()[:Message.MAX_LENGTH]
        if not text:
            return

        message = Message.objects.create(conversation=self.conversation, sender=self.scope['user'], text=text)
        Conversation.objects.filter(pk=self.conversation.pk).update(updated_at=message.created_at)

        async_to_sync(self.channel_layer.group_send)(
            self.group_name, {'type': 'chat.message', 'message': message.to_json()})

    # Called for every 'chat.message' event sent to the group.
    def chat_message(self, event):
        self.send_json(event['message'])
