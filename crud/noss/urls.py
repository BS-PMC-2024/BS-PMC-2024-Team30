from django.contrib import admin
from django.urls import path
from . import views  # Import the home view
from users import views as user_views  # Import the views from the users app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', user_views.login_view, name='login'),
    path('register/', user_views.register_view, name='register'),
]
