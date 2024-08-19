from django.urls import path, include
from . import views
from django.contrib import admin  # ייבוא המודול admin של Django


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('email_verification/', views.email_verification, name='email_verification'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('manager/', views.manager_home, name='manager_home'),
    path('developer/', views.developer_home, name='developer_home'),
    path('logout/', views.logout_view, name='logout'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/settings/', views.project_settings, name='project_settings'),
    path('project/<int:pk>/documents/', views.project_documents, name='project_documents'),
    path('project/<int:pk>/code/', views.project_code, name='project_code'),
    path('project/<int:project_id>/directories/', views.manage_directories, name='manage_directories'),
    path('directory/<int:directory_id>/', views.view_directory, name='view_directory'),
    path('directory/<int:directory_id>/delete/', views.delete_directory, name='delete_directory'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('accounts/', include('allauth.urls')),
    path('project/<int:pk>/file/<int:file_id>/', views.view_file, name='view_file'),
    path('project/<int:project_id>/send_invitation/', views.send_invitation_email, name='send_invitation_email'),
    path('accept_invitation/<int:invitation_id>/', views.accept_invitation, name='accept_invitation'),
    path('download/<int:pk>/<int:file_id>/', views.download_file, name='download_file'),
    path('users/permission-error/<int:pk>/', views.permission_error, name='permission_error'),
    path('file/delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('projects/<int:project_id>/create-task/', views.create_task, name='create_task'),  # יצירת משימה לפרויקט ספציפי
    path('tasks/<int:task_id>/done/', views.mark_task_done, name='mark_task_done'),
    path('my-tasks/', views.developer_tasks, name='developer_tasks'),
    path('projects/<int:project_id>/tasks/', views.project_tasks, name='project_tasks'),
    path('projects/<int:project_id>/ai-code-improvement/', views.ai_code_improvement, name='ai_code_improvement'),
    path('project/<int:project_id>/invite/', views.invite_member, name='invite_member'),
    path('admin/', admin.site.urls),  # זה הנתיב הנכון ל-Django Admin
]
