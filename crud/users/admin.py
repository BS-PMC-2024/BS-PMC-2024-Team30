from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.template.response import TemplateResponse
import csv
from .models import User, Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'created_at')
    search_fields = ('name', 'manager__username')
    list_filter = ('created_at',)

    actions = ['export_user_project_report']

    @admin.action(description='Export Report')
    def export_user_project_report(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="admin_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['User Type', 'Username', 'Email', 'Date Joined', 'Project Count (Managed)', 'Project Count (Involved)'])

        users = User.objects.all()

        for user in users:
            managed_project_count = Project.objects.filter(manager=user).count()
            involved_project_count = user.projects.count()  # מונה את הפרויקטים שבהם המשתמש מעורב

            writer.writerow([
                user.get_persona_display(),
                user.username,
                user.email,
                user.date_joined,
                managed_project_count,
                involved_project_count,
            ])

        return response
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

admin.site.register(User, CustomUserAdmin)
