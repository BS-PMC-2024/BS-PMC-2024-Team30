from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('email_verification/', views.email_verification, name='email_verification'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('manager/', views.manager_home, name='manager_home'),
    path('logout/', views.logout_view, name='logout'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/settings/', views.project_settings, name='project_settings'),
    path('project/<int:pk>/documents/', views.project_documents, name='project_documents'),
    path('project/<int:pk>/code/', views.project_code, name='project_code'),
    path('project/<int:project_id>/upload/', views.upload_code, name='upload_code'),
    path('project/<int:project_id>/directories/', views.manage_directories, name='manage_directories'),
    path('directory/<int:directory_id>/', views.view_directory, name='view_directory'),
    path('directory/<int:directory_id>/delete/', views.delete_directory, name='delete_directory'),
    #add for delete project
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
]
