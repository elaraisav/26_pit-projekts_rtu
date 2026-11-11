import uuid

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

    @property
    def group_name(self):
        """The Channels group both people of the conversation listen to.
        Used by the consumer and by the upload view, so the name lives only here."""
        return f'chat_{self.pk}'


# Random file names, so a stored file's URL can't be guessed from the original name.
# Module-level functions, because migrations refer to them.
def archive_path(instance, filename):
    return f'chat_archives/{uuid.uuid4().hex}.zip'


def thumbnail_path(instance, filename):
    return f'chat_thumbs/{uuid.uuid4().hex}.jpg'


def preview_path(instance, filename):
    return f'chat_previews/{uuid.uuid4().hex}.jpg'


class Message(models.Model):
    MAX_LENGTH = 2000
    TYPE_CHOICES = [
        ('text', 'Teksts'),
        ('payment', 'Maksājuma pieprasījums'),
        ('image', 'Attēlu komplekts'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Gaida apmaksu'),
        ('paid', 'Apmaksāts'),
        ('cancelled', 'Atcelts'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    text = models.TextField(max_length=MAX_LENGTH, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')

    # Payment requests
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    # Only payment requests use the status; it decides whether a batch of images may be uploaded.
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, blank=True)

    # Image batches: one zip with the original files, and the paid request it belongs to.
    archive = models.FileField(upload_to=archive_path, blank=True)
    payment_request = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='batches')

    class Meta:
        ordering = ['created_at']
        constraints = [
            # A payment request pays for one batch only.
            models.UniqueConstraint(fields=['payment_request'], condition=Q(message_type='image'),
                                    name='one_batch_per_payment_request'),
        ]

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

            # Payment requests and image batches
            'type': self.message_type,
            'amount': str(self.payment_amount) if self.payment_amount is not None else None,
            'currency': self.currency,
            'payment_status': self.payment_status,
            'payment_request_id': self.payment_request_id,
            'archive_url': self.archive.url if self.archive else None,
            'images': [
                {'thumbnail': image.thumbnail.url, 'preview': image.preview.url}
                for image in self.images.all()
            ] if self.message_type == 'image' else [],
        }


class MessageImage(models.Model):
    """One picture of an image batch: a small thumbnail for the chat and a larger preview.
    The originals are only in the batch's zip (Message.archive)."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='images')
    thumbnail = models.ImageField(upload_to=thumbnail_path)
    preview = models.ImageField(upload_to=preview_path)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position']


def open_payment_for_upload(conversation):
    """The photographer's latest payment request in the conversation, if it is paid
    and has no image batch yet; otherwise None (no upload allowed)."""
    last = (conversation.messages.filter(message_type='payment', sender_id=conversation.photographer_id)
            .order_by('-created_at', '-pk').first())
    if last is not None and last.payment_status == 'paid' and not last.batches.exists():
        return last
    return None
