from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('email_verification/', views.email_verification, name='email_verification'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('manager/', views.manager_home, name='manager_home'),
    path('logout/', views.logout_view, name='logout'),  # Add this line
]
