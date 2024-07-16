from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from .models import User  # Import the custom User model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from .forms import CustomUserCreationForm, LoginForm, VerificationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is verified
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('users/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(mail_subject, message, 'your_email@example.com', [user.email])
            return redirect('email_verification', uidb64=urlsafe_base64_encode(force_bytes(user.pk)), token=default_token_generator.make_token(user))
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def email_verification(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'users/email_verification.html', {'validlink': False})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    # Send verification email again
                    current_site = get_current_site(request)
                    mail_subject = 'Activate your account.'
                    message = render_to_string('users/acc_active_email.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': default_token_generator.make_token(user),
                    })
                    send_mail(mail_subject, message, 'your_email@example.com', [user.email])
                    return redirect('email_verification', uidb64=urlsafe_base64_encode(force_bytes(user.pk)), token=default_token_generator.make_token(user))
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})
