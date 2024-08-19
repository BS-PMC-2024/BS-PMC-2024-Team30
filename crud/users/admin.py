from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
import csv
from .models import User, Project, Directory, File

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('persona',)}),
    )

    actions = ['export_user_project_report']

    @admin.action(description='Export Report')
    def export_user_project_report(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="admin_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['User Type', 'Username', 'Email', 'Date Joined', 'Project Count', 'Project Names'])

        users = User.objects.all()
        projects = Project.objects.all()

        for user in users:
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


@admin.register(Directory)
class DirectoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'is_deleted')
    search_fields = ('name', 'project__name')
    list_filter = ('is_deleted',)

    actions = ['delete_selected', 'restore_selected']

    @admin.action(description='Soft delete selected directories')
    def delete_selected(self, request, queryset):
        queryset.update(is_deleted=True)

    @admin.action(description='Restore selected directories')
    def restore_selected(self, request, queryset):
        queryset.update(is_deleted=False)

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request).all()
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('file', 'directory', 'uploaded_at', 'is_deleted')
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

admin.site.register(User, CustomUserAdmin)
