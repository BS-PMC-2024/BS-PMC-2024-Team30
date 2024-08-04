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
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='custom_user',
    )

class Project(models.Model):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(User, related_name='managed_projects', on_delete=models.CASCADE)
    team_members = models.ManyToManyField(User, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    VIEW = 'view'
    EDIT = 'edit'
    PERMISSION_CHOICES = [
        (VIEW, 'View'),
        (EDIT, 'Edit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    permission_type = models.CharField(max_length=4, choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = ('user', 'project', 'permission_type')

    def __str__(self):
        return f"{self.user.username} - {self.get_permission_type_display()} - {self.project.name}"
class Directory(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, related_name='directories', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subdirectories', on_delete=models.CASCADE)

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
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=10, choices=[('code', 'Code'), ('document', 'Document')])