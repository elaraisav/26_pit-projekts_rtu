from django.conf import settings
from django.db import models
from django.db.models import Q

# One-on-one chat between a client and a photographer.
# Each client-photographer pair has exactly one conversation.


class ConversationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(Q(client=user) | Q(photographer=user))


class Conversation(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='client_conversations')
    photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='photographer_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    # Moved forward on every new message, so the newest conversation is listed first.
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationQuerySet.as_manager()

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['client', 'photographer'], name='unique_client_photographer'),
        ]

    def __str__(self):
        return f'{self.client} ↔ {self.photographer}'

    @classmethod
    def get_or_create_between(cls, user, other):
        """Return the conversation between two users, creating it if needed.

        Raises ValueError unless one user is a client and the other a photographer.
        """
        if user.is_photographer == other.is_photographer:
            raise ValueError('A conversation needs one client and one photographer.')
        client, photographer = (other, user) if user.is_photographer else (user, other)
        conversation, _ = cls.objects.get_or_create(client=client, photographer=photographer)
        return conversation

    def has_participant(self, user):
        return user.pk in (self.client_id, self.photographer_id)

    def other_participant(self, user):
        return self.photographer if user.pk == self.client_id else self.client


class Message(models.Model):
    MAX_LENGTH = 2000

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    text = models.TextField(max_length=MAX_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender}: {self.text[:40]}'

    def to_json(self):
        """The shape the chat page's JavaScript uses, both for history and live messages."""
        return {
            'id': self.pk,
            'text': self.text,
            'sender_id': self.sender_id,
            'sender_name': self.sender.get_full_name() or self.sender.username,
            'created_at': self.created_at.isoformat(),
        }
