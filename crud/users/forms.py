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
    team_member_emails = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter email addresses separated by commas'}),
        help_text="Enter email addresses separated by commas"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter project description'}),
        required=False,
        help_text="Optional. Enter a brief description of the project."
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'team_member_emails']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project name'}),
        }