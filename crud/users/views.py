from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from .models import User, Project
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .forms import CustomUserCreationForm, LoginForm, VerificationForm, ProjectForm
import uuid
import logging

logger = logging.getLogger(__name__)

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
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    user.verification_code = uuid.uuid4()
                    user.save()
                    logger.debug(f"Generated verification code during login: {user.verification_code} for user: {user.username}")
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
                    return render(request, 'users/login.html', {'form': form, 'error': 'Your account is inactive.'})
            else:
                return render(request, 'users/login.html', {'form': form, 'error': 'Invalid login credentials.'})
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
