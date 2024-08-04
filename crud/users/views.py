from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from .models import User, Project, CodeFile, Directory
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.http import HttpResponseForbidden
from .forms import CustomUserCreationForm, LoginForm, VerificationForm
from .forms import ProjectForm, CodeFileUploadForm, DirectoryForm
import uuid
import logging
from .github_service import GitHubService
from django.conf import settings
from .models import Project  # Make sure to import your Project model

#project delete add"

logger = logging.getLogger(__name__)
@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" has been deleted.')
        return redirect('home')  # or wherever you want to redirect after deletion
    return redirect('project_settings', project_id=project_id)

def upload_code(request, project_id):
    if request.method == 'POST':
        file = request.FILES['file']
        github = GitHubService()
        content = file.read()
        response = github.upload_file(f'project_{project_id}/{file.name}', content)
        if 'content' in response:
            return redirect('project_detail', pk=project_id)
        else:
            return render(request, 'upload.html', {'error': response.get('message')})
    return render(request, 'upload.html')

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'users/project_detail.html', {'project': project})

def project_settings(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'users/project_settings.html', {'project': project})

def project_documents(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'users/project_documents.html', {'project': project})

def manage_directories(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        form = DirectoryForm(request.POST, project=project)
        if form.is_valid():
            directory = form.save(commit=False)
            directory.project = project
            directory.save()
            return redirect('manage_directories', project_id=project.id)
    else:
        form = DirectoryForm(project=project)

    # Fetch only top-level directories for the current project
    directories = Directory.objects.filter(project=project, parent__isnull=True)

    return render(request, 'users/manage_directories.html', {
        'form': form,
        'directories': directories,
        'project': project,
    })

def view_directory(request, directory_id):
    directory = get_object_or_404(Directory, pk=directory_id)

    # Ensure the user has permission to view this directory
    if directory.project.manager != request.user:
        return HttpResponseForbidden("You do not have permission to view this directory.")

    # Collect parent directories for breadcrumb navigation
    breadcrumb = []
    current_directory = directory
    while current_directory:
        breadcrumb.append(current_directory)
        current_directory = current_directory.parent
    breadcrumb.reverse()  # To display in correct order

    return render(request, 'users/view_directory.html', {
        'directory': directory,
        'breadcrumb': breadcrumb,
    })

def delete_directory(request, directory_id):
    directory = get_object_or_404(Directory, pk=directory_id)
    
    #make sure the user has permission to delete this directory
    if directory.project.manager != request.user:
        return HttpResponseForbidden("You do not have permission to delete this directory.")
    
    # Recursive deletion of subdirectories
    def delete_subdirectories(directory):
        for subdirectory in directory.subdirectories.all():
            delete_subdirectories(subdirectory)
        directory.delete()
    
    delete_subdirectories(directory)
    
    return redirect('project_code', pk=directory.project.pk)

def project_code(request, pk):
    project = Project.objects.get(pk=pk)
    if request.method == 'POST':
        form = CodeFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            code_file = form.save(commit=False)
            code_file.directory = Directory.objects.get(pk=request.POST['directory'])
            code_file.save()
            return redirect('project_code', pk=project.pk)
    else:
        form = CodeFileUploadForm()

    directories = project.directories.all()
    files = CodeFile.objects.filter(directory__in=directories)
    return render(request, 'users/project_code.html', {
        'project': project,
        'file_form': form,
        'directories': directories,
        'files': files
    })

@login_required
def manager_home(request):
    if request.user.persona != 'manager':
        return redirect('home')

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.manager = request.user
            project.save()
            emails = form.cleaned_data['team_member_emails'].split(',')
            for email in emails:
                email = email.strip()
                try:
                    user = User.objects.get(email=email)
                    # Send request to join project
                    send_project_request_email(request, user, project)
                except User.DoesNotExist:
                    # Send invitation to sign up and join project
                    send_invitation_email(request, email, project)
            return redirect('manager_home')
    else:
        form = ProjectForm()

    projects = Project.objects.filter(manager=request.user)

    return render(request, 'users/manager_home.html', {'form': form, 'projects': projects})

def send_project_request_email(request, user, project):
    current_site = get_current_site(request)
    mail_subject = f'Invitation to join project {project.name}'
    message = render_to_string('users/project_request_email.html', {
        'user': user,
        'domain': current_site.domain,
        'project': project,
    })
    send_mail(mail_subject, message, 'shohamdimri@gmail.com', [user.email])

def send_invitation_email(request, email, project):
    current_site = get_current_site(request)
    mail_subject = f'Invitation to join {current_site.domain} and project {project.name}'
    message = render_to_string('users/project_invitation_email.html', {
        'domain': current_site.domain,
        'project': project,
        'signup_url': reverse('register'),
    })
    send_mail(mail_subject, message, 'shohamdimri@gmail.com', [email])

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is verified
            user.verification_code = uuid.uuid4()
            user.save()
            logger.debug(f"Generated verification code during registration: {user.verification_code} for user: {user.username}")
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('users/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'token': str(user.verification_code),  # Convert to string
            })
            send_mail(mail_subject, message, 'shohamdimri@gmail.com', [user.email])
            return redirect('email_verification')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def email_verification(request):
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            logger.debug(f"Submitted verification code: {code}")
            try:
                user = User.objects.get(verification_code=uuid.UUID(code))  # Convert to UUID
                logger.debug(f"Retrieved user: {user.username} with verification code: {user.verification_code}")
                if user and not user.is_verified:
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    login(request, user)
                    return redirect('home')
            except (User.DoesNotExist, ValueError):
                logger.debug(f"User does not exist for the provided verification code: {code}")
                pass
        return render(request, 'users/email_verification.html', {'form': form, 'error': 'Invalid verification code'})
    else:
        form = VerificationForm()
    return render(request, 'users/email_verification.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_verified:
                # Generate a new verification code
                user.verification_code = uuid.uuid4()
                user.save()

                # Send the verification code to the user’s email
                mail_subject = 'Your login verification code'
                message = f'Your verification code is {user.verification_code}'
                send_mail(mail_subject, message, 'shohamdimri@gmail.com', [user.email])

                request.session['user_id'] = user.id  # Store user ID in session
                return redirect('verify_code')  # Redirect to code verification page
            else:
                return render(request, 'users/login.html', {'form': form, 'error': 'Invalid username/password or account not verified'})
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def verify_code(request):
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            user_id = request.session.get('user_id')
            try:
                user = User.objects.get(id=user_id, verification_code=code)
                if user:
                    login(request, user)  # Log the user in
                    return redirect('home')
            except User.DoesNotExist:
                pass
        return render(request, 'users/email_verification.html', {'form': form, 'error': 'Invalid verification code'})
    else:
        form = VerificationForm()
    
    return render(request, 'users/email_verification.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')