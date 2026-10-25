from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


# Login form: Django checks the username and password itself.
class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Nepareizs lietotājvārds vai parole.',
        'inactive': 'Šis konts ir deaktivizēts.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Lietotājvārds'
        self.fields['password'].widget.attrs['placeholder'] = 'Parole'


# Registration form: creates a User (password is hashed) with its role.
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label='Vārds', max_length=150)
    last_name = forms.CharField(label='Uzvārds', max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Lietotājvārds',
            'first_name': 'Vārds',
            'last_name': 'Uzvārds',
            'email': 'E-pasts',
            'password1': 'Parole',
            'password2': 'Parole atkārtoti',
        }
        for name, text in placeholders.items():
            self.fields[name].widget.attrs['placeholder'] = text
        # The rules are shown in the error message when a password is rejected.
        self.fields['password1'].help_text = ''

    def clean_username(self):
        # Skip UserCreationForm's duplicate check (see validate_unique below).
        return self.cleaned_data['username']

    def clean_email(self):
        return self.cleaned_data['email'].lower()

    # Username/e-mail uniqueness is not reported here: the view checks it and
    # shows the same page either way, so the form never reveals which accounts exist.
    def validate_unique(self):
        pass
