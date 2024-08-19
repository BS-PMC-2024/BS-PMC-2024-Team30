from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Project


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'blocked')
    list_filter = ('is_staff', 'is_superuser', 'blocked')

    # Add the blocked field to the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('blocked','persona',)}),
)
    
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'created_at')  # Customize the list display as needed
    search_fields = ('name', 'manager__username')     # Add fields to search in the admin interface
    list_filter = ('created_at',)                      # Add filters to the admin interface

admin.site.register(User, CustomUserAdmin)
