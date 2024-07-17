from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    PERSONA_CHOICES = (
        ('manager', 'Manager'),
        ('developer', 'Developer'),
    )
    persona = models.CharField(max_length=10, choices=PERSONA_CHOICES, blank=True, null=True)
    verification_code = models.UUIDField(default=uuid.uuid4, editable=False)
    is_verified = models.BooleanField(default=False)

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
