from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from .models import User
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .forms import CustomUserCreationForm, LoginForm, VerificationForm
import uuid
import logging

logger = logging.getLogger(__name__)

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
                user = User.objects.get(verification_code=code)
                logger.debug(f"Retrieved user: {user.username} with verification code: {user.verification_code}")
                if user and not user.is_verified:
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    login(request, user)
                    return redirect('home')
            except User.DoesNotExist:
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
