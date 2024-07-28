from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Project

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'persona')

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class VerificationForm(forms.Form):
    code = forms.CharField(max_length=36)  # Adjust the max_length if needed

class ProjectForm(forms.ModelForm):
    team_member_emails = forms.CharField(widget=forms.Textarea, help_text="Enter email addresses separated by commas")

    class Meta:
        model = Project
        fields = ['name', 'team_member_emails']
