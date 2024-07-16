from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    persona = forms.ChoiceField(choices=User.PERSONA_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'persona', 'password1', 'password2')

class VerificationForm(forms.Form):
    uidb64 = forms.CharField()
    token = forms.CharField()

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
