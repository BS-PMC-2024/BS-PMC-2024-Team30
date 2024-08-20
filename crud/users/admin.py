from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
import csv
from .models import User, Project, Directory, File
from django.utils.timezone import now
from django.template.response import TemplateResponse
from django.utils.html import format_html
    
# דוח סטטיסטי מותאם
def stats_report(request):
    current_month = now().month
    current_year = now().year

    new_users_count = User.objects.filter(date_joined__month=current_month, date_joined__year=current_year).count()
    new_projects_count = Project.objects.filter(created_at__month=current_month, created_at__year=current_year).count()

    context = {
        'new_users_count': new_users_count,
        'new_projects_count': new_projects_count,
    }

    return TemplateResponse(request, "admin/stats_report.html", context)


# רישום המודלים בממשק Django Admin הרגיל
from .models import User
from .models import Project


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('blocked','persona',)}),
    )
    actions = ['export_user_project_report']

    @admin.action(description='Export Report')
    def export_user_project_report(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="admin_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['User Type', 'Username', 'Email', 'Date Joined', 'Project Count', 'Project Names'])

        #users = User.objects.all()
        projects = Project.objects.all()

        for user in queryset:
            project_count = projects.filter(manager=user).count()
            project_names = ', '.join([project.name for project in projects.filter(manager=user)])
            writer.writerow([
                user.get_persona_display(),
                user.username,
                user.email,
                user.date_joined,
                project_count,
                project_names
            ])

        return response

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'created_at', 'is_deleted')
    search_fields = ('name', 'manager__username')
    list_filter = ('created_at', 'is_deleted')

    actions = ['export_user_project_report', 'delete_selected', 'restore_selected']

    @admin.action(description='Export Report')
    def export_user_project_report(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="admin_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['User Type', 'Username', 'Email', 'Date Joined', 'Project Count (Managed)', 'Project Count (Involved)'])

        users = User.objects.all()

        for user in users:
            managed_project_count = Project.objects.filter(manager=user).count()
            involved_project_count = user.projects.count()

            writer.writerow([
                user.get_persona_display(),
                user.username,
                user.email,
                user.date_joined,
                managed_project_count,
                involved_project_count,
            ])

        return response

    @admin.action(description='Soft delete selected projects')
    def delete_selected(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Restore selected projects')
    def restore_selected(self, request, queryset):
        queryset.update(is_deleted=False)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request).all()
        return super().get_queryset(request).filter(is_deleted=False)

class DirectoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'is_deleted', 'parent', 'get_view_permissions', 'get_edit_permissions')
    search_fields = ('name', 'project__name')
    list_filter = ('is_deleted',)
    filter_horizontal = ['view_permissions', 'edit_permissions']
    
    actions = ['delete_selected', 'restore_selected']

    def get_view_permissions(self, obj):
        return ", ".join([user.username for user in obj.view_permissions.all()])
    get_view_permissions.short_description = 'View Permissions'

    def get_edit_permissions(self, obj):
        return ", ".join([user.username for user in obj.edit_permissions.all()])
    get_edit_permissions.short_description = 'Edit Permissions'

    @admin.action(description='Soft delete selected directories')
    def delete_selected(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Restore selected directories and their contents')
    def restore_selected(self, request, queryset):
        for directory in queryset:
            self._restore_directory(directory)

    def save_model(self, request, obj, form, change):
        # If the directory is being restored (is_deleted is set to False)
        if change and not obj.is_deleted:
            # Restore the directory and its contents
            self._restore_directory(obj)
        else:
            super().save_model(request, obj, form, change)

    def _restore_directory(self, directory):
        # Restore the directory itself
        directory.is_deleted = False
        directory.save()

        # Restore all subdirectories
        subdirectories = directory.subdirectories.filter(is_deleted=True)
        for subdirectory in subdirectories:
            self._restore_directory(subdirectory)

        # Restore all files within this directory
        files = directory.files.filter(is_deleted=True)
        for file in files:
            file.is_deleted = False
            file.save()

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request).all()
        return super().get_queryset(request).filter(is_deleted=False)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ['view_permissions', 'edit_permissions']:
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                directory = Directory.objects.get(pk=obj_id)
                kwargs['queryset'] = directory.project.team_members.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)




@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name_display', 'directory', 'uploaded_at', 'is_deleted')
    search_fields = ('file', 'directory__name')
    list_filter = ('is_deleted',)

    actions = ['delete_selected', 'restore_selected']

    @admin.action(description='Soft delete selected files')
    def delete_selected(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Restore selected files')
    def restore_selected(self, request, queryset):
        queryset.update(is_deleted=False)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request).all()
        return super().get_queryset(request).filter(is_deleted=False)

    def file_name_display(self, obj):
        return format_html("<span>{}</span>", obj.file.name)

    file_name_display.short_description = 'File'

    
admin.site.register(Directory, DirectoryAdmin)
admin.site.register(User, CustomUserAdmin)
