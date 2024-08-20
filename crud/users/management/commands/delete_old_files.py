from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import File, Directory
from users.views import delete_file_from_github, delete_directory_from_github, get_directory_path
from django.conf import settings

class Command(BaseCommand):
    help = 'Delete files and directories that were marked as deleted more than a week ago.'

    def handle(self, *args, **kwargs):
        one_week_ago = timezone.now() - timedelta(days=7)
        access_token = settings.GITHUB_TOKEN
        repo = settings.GITHUB_REPO


        # Delete files that have been marked as deleted for more than a week
        old_files = File.objects.filter(is_deleted=True, deleted_at__lt=one_week_ago)
        file_count = old_files.count()
        for file in old_files:
            file_path = f"{file.directory.project.name}{file.directory.project.id}/{get_directory_path(file.directory)}/{file.file.name}"
            delete_file_from_github(access_token, repo, file_path)

        old_files.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {file_count} old files.'))

        # delete directories that have been marked as deleted for more than a week
        old_directories = Directory.objects.filter(is_deleted=True, deleted_at__lt=one_week_ago)
        directory_count = old_directories.count()
        
        self.stdout.write(self.style.SUCCESS(f'Deleted {directory_count} old directories.'))
        
           
        # Delete subdirectories and files
        for directory in old_directories:
            try:
                # Delete subdirectories and files
                for subdirectory in directory.subdirectories.all():
                    delete_directory_from_github(access_token, repo, f"{directory.project.name}{directory.project.id}/{get_directory_path(subdirectory)}")
                    subdirectory.delete()

                for file in directory.files.all():
                    file_path = f"{directory.project.name}{directory.project.id}/{get_directory_path(directory)}/{file.file.name}"
                    delete_file_from_github(access_token, repo, file_path)
                    file.delete()

                # Finally delete the directory itself
                delete_directory_from_github(access_token, repo, f"{directory.project.name}{directory.project.id}/{get_directory_path(directory)}")
                directory.delete()

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error deleting directory '{directory.name}': {e}"))