from django.test import TestCase
from django.urls import reverse

from .models import User


class RegistrationTests(TestCase):
    data = {
        'username': 'anna', 'first_name': 'Anna', 'last_name': 'Ozola',
        'email': 'anna@example.com', 'role': 'client',
        'password1': 'Drosa-parole-731', 'password2': 'Drosa-parole-731',
    }

    def register(self, **changes):
        return self.client.post(reverse('testsite:registracija'), {**self.data, **changes})

    def test_new_user_is_created_but_not_logged_in(self):
        response = self.register()
        self.assertRedirects(response, reverse('testsite:registracija_nosutita'))
        self.assertTrue(User.objects.filter(username='anna').exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_duplicate_email_or_username_creates_nothing_and_looks_identical(self):
        self.register()
        for changes in ({'username': 'cita'}, {'email': 'cita@example.com'}, {'email': 'ANNA@example.com', 'username': 'cita'}):
            response = self.register(**changes)
            self.assertRedirects(response, reverse('testsite:registracija_nosutita'))
        self.assertEqual(User.objects.count(), 1)

    def test_login_works_after_registration(self):
        self.register()
        self.assertTrue(self.client.login(username='anna', password='Drosa-parole-731'))
