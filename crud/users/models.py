from django.contrib.auth.models import AbstractUser
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

# models.py
class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)  # Added description field
    manager = models.ForeignKey(User, related_name='managed_projects', on_delete=models.CASCADE)
    team_members = models.ManyToManyField(User, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

