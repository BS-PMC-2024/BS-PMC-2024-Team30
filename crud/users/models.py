from django.contrib.auth.models import AbstractUser, User
from django.db import models
import uuid

class User(AbstractUser):
    PERSONA_CHOICES = (
        ('manager', 'Manager'),
        ('developer', 'Developer'),
    )
    persona = models.CharField(max_length=10, choices=PERSONA_CHOICES, blank=True, null=True)
    verification_code = models.UUIDField(default=uuid.uuid4)
    is_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    blocked = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        related_query_name='custom_user',
    )


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(User, related_name='managed_projects', on_delete=models.CASCADE)
    team_members = models.ManyToManyField(User, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Invitation(models.Model):
    email = models.EmailField()
    project = models.ForeignKey(Project, related_name='invitations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    
class Directory(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, related_name='directories', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subdirectories', on_delete=models.CASCADE)
    view_permissions = models.ManyToManyField(User, related_name='viewable_directories', blank=True)
    edit_permissions = models.ManyToManyField(User, related_name='editable_directories', blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.name

    @property
    def full_path(self):
        if self.parent:
            return f"{self.parent.full_path}/{self.name}"
        return self.name

class File(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='files/')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=10, choices=[('code', 'Code'), ('document', 'Document')])

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)  # קישור ל-Project
    assigned_to = models.ManyToManyField(User, related_name='tasks')  # רשימת מפתחים
    created_by = models.ForeignKey(User, related_name='created_tasks', on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:50]}"