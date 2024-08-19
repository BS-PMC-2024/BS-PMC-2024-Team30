from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Project, File, Directory, Invitation
import os
from .models import Task
from django import forms
from .models import Task

from .models import Task, Project, User



class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'persona')

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class VerificationForm(forms.Form):
    code = forms.CharField(max_length=36)  # Adjust the max_length if needed
    
from django import forms
from .models import Project
#פה היה שינוי
class ProjectForm(forms.ModelForm):
    team_member_emails = forms.EmailField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'width: 100%; max-width: 300px;',
            'placeholder': 'Enter email'
        }),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter project description'
        }),
        required=False,
        help_text="Optional. Enter a brief description of the project."
    )
#פה היה שינוי
    class Meta:
        model = Project
        fields = ['name', 'description', 'team_member_emails']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'width: 100%; max-width: 300px;',
                'placeholder': 'Enter Project name'
            }),
        }

class InviteMemberForm(forms.Form):
    email = forms.EmailField(
        label="Team Member Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': "Enter team member's email"
        }),
        required=True
    )

class CodeFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file', 'directory']
        widgets = {
            'directory': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if project and user != project.manager:
             self.fields['directory'].queryset = Directory.objects.filter(
                project=project,
                edit_permissions=user
            )
        elif project and user == project.manager:
            self.fields['directory'].queryset = Directory.objects.filter(
                project=project,
            )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            allowed_extensions = ['.py', '.js', '.java', '.c', '.cpp', '.html', '.css']
            extension = os.path.splitext(file.name)[1].lower()
            if extension not in allowed_extensions:
                raise forms.ValidationError('Invalid file type. Please upload a code file.')
        return file
    
class DocumentFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file']
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
    
class UserPermissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        user = kwargs.pop('user', None)
        permission_type = kwargs.pop('permission_type', None)
        super().__init__(*args, **kwargs)
        
        if user and permission_type and project:
            project_members = project.team_members.all()
            if permission_type == 'view':
                self.fields['view_permissions'] = forms.ModelMultipleChoiceField(
                    queryset=project_members.exclude(user_id=project.manager.id),
                    required=False,
                    widget=forms.CheckboxSelectMultiple
                )
            elif permission_type == 'edit':
                self.fields['edit_permissions'] = forms.ModelMultipleChoiceField(
                    queryset=project_members.exclude(user_id=project.manager.id),
                    required=False,
                    widget=forms.CheckboxSelectMultiple
                )

    
class DirectoryManagementForm(forms.ModelForm):
    view_permissions = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    edit_permissions = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['parent'].queryset = Directory.objects.filter(project=project)
            project_members = project.team_members.all()
            
            # Set the queryset for view and edit permissions fields
            self.fields['view_permissions'].queryset = project_members.exclude(id=project.manager.id)
            self.fields['edit_permissions'].queryset = project_members.exclude(id=project.manager.id)
    
    class Meta:
        model = Directory
        fields = ['name', 'parent', 'view_permissions', 'edit_permissions']
        widgets = {
            'parent': forms.Select(attrs={'class': 'form-control'})
        }

class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['email']
        
class EditFileForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea, label="File Content")
 

class TaskForm(forms.ModelForm):
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # נעדכן את זה ב-View
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Assign to Developers"
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # מקבלים את המשתמש מה-View
        super(TaskForm, self).__init__(*args, **kwargs)
        if user:
            # מציג רק את המשתמשים שמשויכים לפרויקטים שהמנהל הנוכחי יצר
            self.fields['assigned_to'].queryset = User.objects.filter(projects__manager=user).distinct()
