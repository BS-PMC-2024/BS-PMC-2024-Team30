from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('manager/', views.manager_home, name='manager_home'),
    path('developer/', views.developer_home, name='developer_home'),
    path('users/', include('users.urls')),  # Include the users app URLs
]
