from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Project, File, Directory
import os

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
        
class CodeFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file', 'directory']
        widgets = {
            'directory': forms.Select(attrs={'class': 'form-control'})
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check if file extension is one of the accepted code file extensions
            allowed_extensions = ['.py', '.js', '.java', '.c', '.cpp', '.html', '.css']
            extension = os.path.splitext(file.name)[1].lower()
            if extension not in allowed_extensions:
                raise forms.ValidationError('Invalid file type. Please upload a code file.')
        return file
    
class DocumentFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file', 'directory']
        widgets = {
            'directory': forms.Select(attrs={'class': 'form-control'})
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check if file extension is one of the accepted document file extensions
            allowed_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
            extension = os.path.splitext(file.name)[1].lower()
            if extension not in allowed_extensions:
                raise forms.ValidationError('Invalid file type. Please upload a document file.')
        return file
    
class DirectoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['parent'].queryset = Directory.objects.filter(project=project)
    
    class Meta:
        model = Directory
        fields = ['name', 'parent']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-control'})
        }