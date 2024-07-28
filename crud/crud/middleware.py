from django.shortcuts import redirect
from django.urls import reverse

class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            if request.path not in [reverse('email_verification'), reverse('logout')]:
                return redirect('email_verification')
        response = self.get_response(request)
        return response
