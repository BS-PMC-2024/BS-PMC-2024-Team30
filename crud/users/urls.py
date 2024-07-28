from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('email_verification/', views.email_verification, name='email_verification'),
    path('verify-code/', views.verify_code, name='verify_code'),
]
