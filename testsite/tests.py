from django.test import TestCase
from django.urls import reverse

from .models import Photographer, User


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


class PhotographerProfileTests(TestCase):
    url = reverse('testsite:profila_regid')

    def setUp(self):
        self.photographer = User.objects.create_user(
            'foto', 'foto@example.com', 'Drosa-parole-731', role=User.PHOTOGRAPHER)
        self.client.force_login(self.photographer)

    def test_description_is_saved_and_shown_on_the_profile(self):
        response = self.client.post(self.url, {'description': 'Kāzu fotogrāfs'}, follow=True)
        self.assertRedirects(response, reverse('testsite:profils_fotogr'))
        self.assertEqual(Photographer.objects.get(user=self.photographer).description, 'Kāzu fotogrāfs')
        self.assertContains(response, 'Kāzu fotogrāfs')

    def test_description_over_250_characters_is_rejected_with_the_design_message(self):
        response = self.client.post(self.url, {'description': 'a' * 251})
        self.assertContains(response, 'Apraksts nedrīkst pārsniegt 250 rakstzīmes!')
        self.assertEqual(Photographer.objects.get(user=self.photographer).description, '')

    def test_textarea_has_no_maxlength_so_the_browser_does_not_hide_the_message(self):
        self.assertNotContains(self.client.get(self.url), 'maxlength')

    def test_description_of_exactly_250_characters_is_saved(self):
        self.client.post(self.url, {'description': 'a' * 250})
        self.assertEqual(len(Photographer.objects.get(user=self.photographer).description), 250)

    def test_visitor_who_is_not_logged_in_is_sent_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {'description': 'x'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('testsite:autorizacija'), response.url)
        self.assertEqual(Photographer.objects.count(), 0)

    def test_client_has_no_profile_to_edit(self):
        client_user = User.objects.create_user('klients', 'klients@example.com', 'Drosa-parole-731')
        self.client.force_login(client_user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'description': 'x'}).status_code, 404)
        self.assertEqual(Photographer.objects.count(), 0)

    def test_client_has_no_photographer_profile_page(self):
        client_user = User.objects.create_user('klients', 'klients@example.com', 'Drosa-parole-731')
        self.client.force_login(client_user)
        self.assertEqual(self.client.get(reverse('testsite:profils_fotogr')).status_code, 404)

    def test_photographer_without_a_saved_profile_sees_the_page(self):
        response = self.client.get(reverse('testsite:profils_fotogr'))
        self.assertContains(response, 'Apraksts vēl nav pievienots.')

    def test_photographer_only_changes_their_own_profile(self):
        other = User.objects.create_user('cits', 'cits@example.com', 'Drosa-parole-731', role=User.PHOTOGRAPHER)
        Photographer.objects.create(user=other, description='Cita apraksts')
        self.client.post(self.url, {'description': 'Mans apraksts'})
        self.assertEqual(Photographer.objects.get(user=other).description, 'Cita apraksts')
        self.assertEqual(Photographer.objects.get(user=self.photographer).description, 'Mans apraksts')
