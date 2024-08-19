
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.http import HttpResponse
# import csv
# from .models import User, Project

# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     list_display = ('name', 'manager', 'created_at')
#     search_fields = ('name', 'manager__username')
#     list_filter = ('created_at',)

#     actions = ['export_user_project_report']

#     @admin.action(description='Export Report')
#     def export_user_project_report(self, request, queryset):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="admin_report.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['User Type', 'Username', 'Email', 'Date Joined', 'Project Count', 'Project Names'])

#         users = User.objects.all()
#         projects = Project.objects.all()

#         for user in users:
#             project_count = projects.filter(manager=user).count()
#             project_names = ', '.join([project.name for project in projects.filter(manager=user)])
#             writer.writerow([
#                 user.get_persona_display(),
#                 user.username,
#                 user.email,
#                 user.date_joined,
#                 project_count,
#                 project_names
#             ])

#         return response

# class CustomUserAdmin(UserAdmin):
#     fieldsets = UserAdmin.fieldsets + (
#         (None, {'fields': ('persona',)}),
#     )

#     actions = ['export_user_project_report']

#     @admin.action(description='Export Report')
#     def export_user_project_report(self, request, queryset):
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="admin_report.csv"'

#         writer = csv.writer(response)
#         writer.writerow(['User Type', 'Username', 'Email', 'Date Joined', 'Project Count', 'Project Names'])

#         users = User.objects.all()
#         projects = Project.objects.all()

#         for user in users:
#             project_count = projects.filter(manager=user).count()
#             project_names = ', '.join([project.name for project in projects.filter(manager=user)])
#             writer.writerow([
#                 user.get_persona_display(),
#                 user.username,
#                 user.email,
#                 user.date_joined,
#                 project_count,
#                 project_names
#             ])

#         return response

# admin.site.register(User, CustomUserAdmin)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.template.response import TemplateResponse
import csv
from .models import User, Project
from django.utils.timezone import now


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
    list_display = ('username', 'email', 'is_staff', 'blocked')
    list_filter = ('is_staff', 'is_superuser', 'blocked')

    # Add the blocked field to the admin form
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


admin.site.register(User, CustomUserAdmin)
