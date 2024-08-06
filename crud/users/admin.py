from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Project  # Import your Project model

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'created_at')  # Customize the list display as needed
    search_fields = ('name', 'manager__username')     # Add fields to search in the admin interface
    list_filter = ('created_at',)                      # Add filters to the admin interface
    
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('persona',)}),
    )

admin.site.register(User, CustomUserAdmin)
