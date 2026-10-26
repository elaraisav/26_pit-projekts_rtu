from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

# One-on-one chat between a client and a photographer.
# Each client-photographer pair has exactly one conversation.

# The one rule for who may chat: active, non-admin accounts.
# can_chat, can_chat_together and chat_partners_for are used everywhere
# (views, consumer, model, admin), so the rule only lives here.
NOT_ALLOWED_STAFF = 'Administratoru konti sarakstē nepiedalās.'
NOT_ALLOWED_ROLES = 'Sarunu var sākt tikai starp klientu un fotogrāfu.'


def can_chat(user):
    return bool(user.is_authenticated and user.is_active and not user.is_staff and not user.is_superuser)


def can_chat_together(user, other):
    return can_chat(user) and can_chat(other) and user.is_photographer != other.is_photographer


def chat_problem(user, other):
    """The Latvian reason why two users can't chat, or None if they can."""
    if not (can_chat(user) and can_chat(other)):
        return NOT_ALLOWED_STAFF
    if user.is_photographer == other.is_photographer:
        return NOT_ALLOWED_ROLES
    return None


def chat_users():
    """All users who may take part in the chat (the queryset form of can_chat)."""
    return get_user_model().objects.filter(is_active=True, is_staff=False, is_superuser=False)


def chat_partners_for(user):
    """Users of the other role that user may chat with."""
    other_role = get_user_model().CLIENT if user.is_photographer else get_user_model().PHOTOGRAPHER
    return chat_users().filter(role=other_role)


class ConversationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(Q(client=user) | Q(photographer=user))

    def usable(self):
        """Conversations where both sides may still chat (e.g. nobody became an admin since)."""
        return self.filter(client__in=chat_users(), photographer__in=chat_users())


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

        Raises ValueError (with a Latvian reason for the user) unless one user is a
        client and the other a photographer, and neither is an admin account.
        """
        problem = chat_problem(user, other)
        if problem:
            raise ValueError(problem)
        client, photographer = (other, user) if user.is_photographer else (user, other)
        conversation, _ = cls.objects.get_or_create(client=client, photographer=photographer)
        return conversation

    def clean(self):
        # Runs for conversations made in /admin/, which doesn't use get_or_create_between.
        if self.client_id and self.photographer_id:
            if self.client.is_photographer or not self.photographer.is_photographer:
                raise ValidationError(NOT_ALLOWED_ROLES)
            if not (can_chat(self.client) and can_chat(self.photographer)):
                raise ValidationError(NOT_ALLOWED_STAFF)

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
