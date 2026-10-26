from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
# Our own user model, set as AUTH_USER_MODEL in settings.py. Django recommends
# this from the start of a project: changing the user model after the first
# migrations is very hard. AbstractUser already has username, password,
# first/last name and e-mail; here we add the role and make e-mail unique.
class User(AbstractUser):
    CLIENT = 'client'
    PHOTOGRAPHER = 'photographer'
    ROLE_CHOICES = [
        (CLIENT, 'Klients'),
        (PHOTOGRAPHER, 'Fotogrāfs'),
    ]

    email = models.EmailField('E-pasts', unique=True)
    role = models.CharField('Loma', max_length=20, choices=ROLE_CHOICES, default=CLIENT)

    @property
    def is_photographer(self):
        return self.role == self.PHOTOGRAPHER
