import os
import uuid
import logging
import requests
import base64
import openai
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.http import (
    HttpResponseForbidden, Http404, HttpResponseRedirect, 
    HttpResponse, JsonResponse
)
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib import messages

from .models import User, Project, File, Directory, Invitation, Task, Notification
from .forms import (
    CustomUserCreationForm, LoginForm, TaskForm, VerificationForm, 
    InvitationForm, ProjectForm, UserPermissionForm, 
    EditFileForm, DocumentFileForm, CodeFileForm, DirectoryManagementForm
)
from .github_service import GitHubService




logger = logging.getLogger(__name__)
@login_required
# views.py

def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, manager=request.user)
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" has been deleted.')
        return redirect('home')  # or wherever you want to redirect after deletion
    return redirect('project_settings', pk=project_id)


def get_file_from_github(access_token, repo, file_path):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_data = response.json()
        file_content = base64.b64decode(file_data['content']).decode('utf-8')
        return file_content
    else:
        response.raise_for_status()

def delete_file_from_github(access_token, repo, file_path):
    """
    Delete a single file from GitHub.
    """
    url = f'https://api.github.com/repos/{repo}/contents/{file_path}'
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    sha = get_sha_of_path(access_token, repo, file_path)
    if sha is None:
        print(f"Skipping deletion of file {file_path} as it does not exist.")
        return

    delete_response = requests.delete(url, headers=headers, json={
        'message': 'Deleting file',
        'sha': sha
    })
    
    if delete_response.status_code == 422:
        print("Error details:", delete_response.json())
        raise Exception(f"Unprocessable Entity: {delete_response.json()}")
    
    delete_response.raise_for_status()
    print(f"File {file_path} successfully deleted.")

    
def download_file(request, pk, file_id):
    file = get_object_or_404(File, id=file_id)
    project = get_object_or_404(Project, id=pk)
    url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/{project.name}{project.id}/{file.directory}/{file.file.name[6:]}"
    file_path = file.file.path
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    # Serve the file
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
@login_required
def view_file(request, pk, file_id):
    project = get_object_or_404(Project, pk=pk, is_deleted=False)
    file = get_object_or_404(File, id=file_id, is_deleted=False)
    access_token = settings.GITHUB_TOKEN
    repo = settings.GITHUB_REPO
    filename = file.file.name[6:]
    directory_path = get_directory_path(file.directory)
    
    if request.method == 'POST':
        if request.user not in file.directory.edit_permissions.all():
            messages.warning(request, "You do not have permission to edit this file.")
            return redirect('view_file', pk=pk, file_id=file_id)
        file_content = request.POST.get('file_content', '')

        try:
            # Update the file content on GitHub
            update_file_on_github(access_token, repo, f"{project.name}{project.id}/{directory_path}/{filename}", file_content)
            return redirect('view_file', pk=pk, file_id=file_id)
        except requests.exceptions.HTTPError as http_err:
            return HttpResponse(f"HTTP error occurred: {http_err}", status=500)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred: {e}", status=500)
    else:
        try:
            file_content = get_file_from_github(access_token, repo, f"{project.name}{project.id}/{directory_path}/{filename}")
            return render(request, 'users/view_file.html', {'project': project, 'file_content': file_content, 'file_name': filename, 'file_id': file_id})
        except requests.exceptions.HTTPError as http_err:
            return HttpResponse(f"HTTP error occurred: {http_err}", status=500)
        except Exception as e:
            return HttpResponse(f"An unexpected error occurred: {e}", status=500)
                
def update_file_on_github(access_token, repo, path, content):
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get the SHA of the file to update
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    sha = response.json().get('sha')

    data = {
        'message': 'Update file content',
        'content': base64.b64encode(content.encode()).decode(),
        'sha': sha
    }
    
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    
#helper function to get path of a file or directory
def get_directory_path(directory):
    path_parts = []
    while directory:
        path_parts.append(directory.name)
        directory = directory.parent
    return '/'.join(reversed(path_parts))


def upload_file_to_github(access_token, path, content, message="Initial commit"):
    url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    if isinstance(content, str):
        content = content.encode('utf-8')
    encoded_content = base64.b64encode(content).decode('utf-8')
    data = {
        "message": message,
        "content": encoded_content
    }
    response = requests.put(url, headers=headers, json=data)
    return response.json()

def create_directory_on_github(access_token, dir_path):
    content = "this is a directory."
    file_path = f"{dir_path}/README.md"
    return upload_file_to_github(access_token, file_path, content, "create directory")

@login_required
def manage_directories(request, project_id):
    
    project = get_object_or_404(Project, pk=project_id, is_deleted=False)
    if request.user != project.manager:
        return redirect('project_detail', pk=project_id)
    
    if request.method == 'POST':
        form = DirectoryManagementForm(request.POST, project=project)
        if form.is_valid():
            directory = form.save(commit=False)
            directory.project = project

            directory_path = get_directory_path(directory)

            try:
                access_token = settings.GITHUB_TOKEN
                if not access_token:
                    raise ValueError("GitHub access token is not configured.")

                create_directory_on_github(access_token, f"{project.name}{project.id}/{directory_path}")

                # Save the directory only if the GitHub operation is successful
                directory.save()

                # Handle permission assignment
                view_permissions = form.cleaned_data['view_permissions']
                edit_permissions = form.cleaned_data['edit_permissions']

                for user in view_permissions:
                    directory.view_permissions.add(user)
                for user in edit_permissions:
                    directory.edit_permissions.add(user)

                # Copy permissions to subdirectories if needed
                if directory.parent:
                    copy_permissions(directory.parent, directory)

            except ValueError as e:
                return HttpResponse(f"Error: {e}", status=400)
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}", status=500)

            return redirect('manage_directories', project_id=project.id)
    else:
        form = DirectoryManagementForm(project=project)

    directories = Directory.objects.filter(project=project, parent__isnull=True, is_deleted=False)
    return render(request, 'users/manage_directories.html', {
        'form': form,
        'directories': directories,
        'project': project,
    })

def copy_permissions(parent_directory, new_directory):
    #copy view permissions from parent directories
    for user in parent_directory.view_permissions.all():
        new_directory.view_permissions.add(user)
    
    #copy edit permissions from parent directories
    for user in parent_directory.edit_permissions.all():
        new_directory.edit_permissions.add(user)    
    
def permission_error(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'users/permission_error.html', {
        "project": project
    })

def permission_handler(directory, user, permission_type):
    #give permissions to subdirectories
    if permission_type == 'view':
        directory.view_permissions.add(user)
    elif permission_type == 'edit':
        directory.edit_permissions.add(user)
    
    for subdirectory in directory.subdirectories.all():
        if permission_type == 'view':
            subdirectory.view_permissions.add(user)
        elif permission_type == 'edit':
            subdirectory.edit_permissions.add(user)
        permission_handler(subdirectory, user, permission_type)

@login_required
def view_directory(request, directory_id):
    directory = get_object_or_404(Directory, id=directory_id, is_deleted=False)
    project = directory.project
    if request.user != project.manager:
        #return redirect('project_detail', pk=project.id)
         raise PermissionDenied  # Raise PermissionDenied instead of redirecting

    if request.method == 'POST':
        if 'add_view_permission' in request.POST:
            view_permissions = request.POST.getlist('view_permissions')
            for user_id in view_permissions:
                if user_id.isdigit():
                    user = get_object_or_404(User, id=int(user_id))
                    directory.view_permissions.add(user)
        
        if 'remove_view_permissions' in request.POST:
            remove_view_permissions = request.POST.getlist('remove_view_permissions')
            for user_id in remove_view_permissions:
                if user_id.isdigit():
                    user = get_object_or_404(User, id=int(user_id))
                    directory.view_permissions.remove(user)
        
        if 'add_edit_permission' in request.POST:
            edit_permissions = request.POST.getlist('edit_permissions')
            for user_id in edit_permissions:
                if user_id.isdigit():
                    user = get_object_or_404(User, id=int(user_id))
                    directory.edit_permissions.add(user)
        
        if 'remove_edit_permissions' in request.POST:
            remove_edit_permissions = request.POST.getlist('remove_edit_permissions')
            for user_id in remove_edit_permissions:
                if user_id.isdigit():
                    user = get_object_or_404(User, id=int(user_id))
                    directory.edit_permissions.remove(user)

        if 'delete_file' in request.POST:
            file_id = request.POST.get('file_id')
            if file_id.isdigit():
                file = get_object_or_404(File, id=int(file_id))
                repo = settings.GITHUB_REPO
                access_token = settings.GITHUB_TOKEN
                directory_path = get_directory_path(file.directory)
                file_path = f"{directory.project.name}{directory.project.id}/{directory_path}/{file.file.name}"
                # try:
                #     delete_file_from_github(access_token, repo, file_path)
                # except Exception as e:
                #     return HttpResponse(f"An error occurred while deleting the file from GitHub: {e}", status=500)
                file_del(request, file)

        if 'delete_directory' in request.POST:
            if request.user == directory.project.manager or request.user in directory.edit_permissions.all():
                access_token = settings.GITHUB_TOKEN
                repo = settings.GITHUB_REPO
                try:
                    # Delete subdirectories and files
                    for subdirectory in directory.subdirectories.all():
                        #delete_directory_from_github(access_token, repo, f"{directory.project.name}{directory.project.id}/{get_directory_path(subdirectory)}")
                        #subdirectory.delete()
                        subdirectory.is_delete = True
                        subdirectory.deleted_at = timezone.datetime.now()
                        subdirectory.save()
                    for file in directory.files.all():
                        #file_path = f"{directory.project.name}{directory.project.id}/{get_directory_path(directory)}/{file.file.name}"
                        #delete_file_from_github(access_token, repo, file_path)
                        #file.delete()
                        print(file.file.name)
                        file.is_deleted = True
                        file.deleted_at = timezone.datetime.now()
                        file.save()
                    # Finally delete the directory itself
                    #delete_directory_from_github(access_token, repo, f"{directory.project.name}{directory.project.id}/{get_directory_path(directory)}")
                    #directory.delete()
                    directory.is_deleted = True
                    directory.deleted_at = timezone.datetime.now()
                    directory.save()
                except Exception as e:
                    return HttpResponse(f"An error occurred: {e}", status=500)
                return redirect('manage_directories', project_id=directory.project.id)
            else:
                return HttpResponse("You do not have permission to delete this directory.", status=403)

        # Redirect to avoid resubmission on refresh
        return redirect('view_directory', directory_id=directory.id)

    # Form handling for adding permissions
    view_form = UserPermissionForm(user=request.user, permission_type='view', initial={'view_permissions': directory.view_permissions.all()})
    edit_form = UserPermissionForm(user=request.user, permission_type='edit', initial={'edit_permissions': directory.edit_permissions.all()})

    breadcrumb = get_directory_breadcrumb(directory)

    return render(request, 'users/view_directory.html', {
        'directory': directory,
        'breadcrumb': breadcrumb,
        'view_form': view_form,
        'edit_form': edit_form,
        'project': project,
    })

def get_directory_breadcrumb(directory):
    breadcrumb = []
    while directory:
        breadcrumb.append(directory)
        directory = directory.parent
    return breadcrumb[::-1]


def delete_directory_from_github(access_token, repo, dir_path):
    """
    Recursively delete a directory and its contents from GitHub.
    """
    url_base = f'https://api.github.com/repos/{repo}/contents/'
    deleted_paths = set()

    def delete_contents(path):
        # Get the contents of the directory
        contents_url = url_base + path
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        
        response = requests.get(contents_url, headers=headers)
        if response.status_code == 404:
            print(f"Directory {path} not found on GitHub.")
            return
        response.raise_for_status()
        
        contents = response.json()
        
        if not isinstance(contents, list):
            raise ValueError(f'Expected a list of contents at {contents_url}.')

        for item in contents:
            item_path = item['path']
            item_type = item['type']
            
            if item_type == 'file':
                delete_file_from_github(access_token, repo, item_path)
            elif item_type == 'dir':
                delete_contents(item_path)
        
        # Now delete the directory itself if not already deleted
        if path not in deleted_paths:
            sha = get_sha_of_path(access_token, repo, path)
            if sha is None:
                print(f"Skipping deletion of directory {path} as it does not exist.")
                return
            
            delete_url = url_base + path
            delete_response = requests.delete(delete_url, headers=headers, json={
                'message': 'Deleting directory',
                'sha': sha
            })
            
            if delete_response.status_code == 422:
                print("Error details:", delete_response.json())
                raise Exception(f"Unprocessable Entity: {delete_response.json()}")
            
            delete_response.raise_for_status()
            print(f"Directory {path} successfully deleted.")
            deleted_paths.add(path)
    
    delete_contents(dir_path)

    
def get_sha_of_path(access_token, repo, path):
    """
    Retrieve the SHA of a file or directory from GitHub.
    """
    url = f'https://api.github.com/repos/{repo}/contents/{path}'
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        print(f"Path {path} not found on GitHub.")
        return None
    response.raise_for_status()
    
    item_info = response.json()
    
    if 'sha' in item_info:
        return item_info['sha']

def delete_directory(request, directory_id):
    directory = get_object_or_404(Directory, pk=directory_id)
    
    if directory.project.manager != request.user:
        return HttpResponseForbidden("You do not have permission to delete this directory.")

    access_token = settings.GITHUB_TOKEN
    repo = settings.GITHUB_REPO

    try:
        delete_directory_from_github(access_token, repo, f"{directory.project.name}{directory.project.id}/{get_directory_path(directory)}")
        
        delete_directory_from_database(directory)
        
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}", status=500)
    
    return redirect('project_code', pk=directory.project.pk)

def delete_directory_from_database(directory):
    """
    Recursively delete a directory and its contents from the database.
    """
    def delete_subdirectories(directory):
        # Delete all files in the directory
        directory.files.all().delete()
        
        # Recursively delete all subdirectories
        for subdirectory in directory.subdirectories.all():
            delete_subdirectories(subdirectory)
        
        # Finally, delete the directory itself
        directory.delete()
    
    delete_subdirectories(directory)
@login_required
def project_documents(request, pk):
    project = get_object_or_404(Project, pk=pk, is_deleted=False)
    
    # Get all document files for the project that are not deleted
    document_files = File.objects.filter(project=project, file_type='document', is_deleted=False)

    if request.method == 'POST':
        form = DocumentFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Save form data without committing to the database yet
            file = form.save(commit=False)
            file.project = project
            
            # Get or create the 'project_documents' directory
            document_directory, created = Directory.objects.get_or_create(
                project=project,
                name='project_documents',
                is_deleted=False
            )

            # Extract file name and extension
            root, extension = os.path.splitext(file.file.name)
            document_type = request.POST.get('document_type', 'document')
            file.directory = document_directory
            file.file.name = document_type + extension
            file.file_type = "document"

            existing_file = File.objects.filter(
                project=project,
                file_type='document',
                directory=document_directory,
                file__icontains=document_type[:8],
                is_deleted=False
            ).first()

            if existing_file:
                existing_file.delete()

            file.save()

            try:
                access_token = settings.GITHUB_TOKEN
                if not access_token:
                    raise ValueError("GitHub access token is not configured.")

                # Define the path for the file on GitHub
                directory_path = get_directory_path(file.directory)
                filename = file.file.name[6:]  # Adjust based on your filename structure
                file_content = file.file.read()
                
                # Upload the new file to GitHub
                upload_file_to_github(
                    access_token,
                    f"{project.name}{project.id}/{directory_path}/{filename}",
                    file_content,
                    "Document upload"
                )

            except ValueError as e:
                return HttpResponse(f"Error: {e}", status=400)
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}", status=500)

            return redirect('project_documents', pk=project.id)
    else:
        form = DocumentFileForm()

    return render(request, 'users/project_documents.html', {
        'form': form,
        'project': project,
        'document_files': document_files,
    })
        
def file_del(request, file):
    users_with_view_permission = file.directory.view_permissions.all()
    directory = file.directory  # Ensure the file has a directory attribute
    # Check if the user is the project manager or has edit permissions for the directory
    if request.user == file.project.manager or request.user in directory.edit_permissions.all():
        directory_name = file.directory.name
        print(directory_name)
        file_name = file.file.name
            #repo = settings.GITHUB_REPO
            #access_token = settings.GITHUB_TOKEN
            #directory_path = get_directory_path(file.directory)
            #file_path = f"{directory.project.name}{directory.project.id}/{directory_path}/{file.file.name}"
            #delete_file_from_github(access_token, repo, file_path)
        
        file.is_deleted = True
        file.deleted_at = timezone.now()
        file.save()
        for user in users_with_view_permission:
            print(user.email)
            if request.user != user:
                Notification.objects.create(
                    user=user,
                    message=f"A file - {file_name} has been deleted from directory {directory_name}"
                )
                print(user.email)
                send_mail('A file was deleted in your project', f"A file - {file_name} has been deleted from directory {directory_name}", settings.EMAIL_USER, [user.email])
    return
def delete_file(request, file_id):
    if request.method == 'POST':
        
        file = get_object_or_404(File, id=file_id)
        file_del(request,file)
        return redirect('project_code', pk=file.project.pk)
        # file = get_object_or_404(File, id=file_id)
        # users_with_view_permission = file.directory.view_permissions.all()
        # directory = file.directory  # Ensure the file has a directory attribute
        # # Check if the user is the project manager or has edit permissions for the directory
        # if request.user == file.project.manager or request.user in directory.edit_permissions.all():
        #     directory_name = file.directory.name
        #     print(directory_name)
        #     file_name = file.file.name
        #     try:
        #         #repo = settings.GITHUB_REPO
        #         #access_token = settings.GITHUB_TOKEN
        #         #directory_path = get_directory_path(file.directory)
        #         #file_path = f"{directory.project.name}{directory.project.id}/{directory_path}/{file.file.name}"
        #         #delete_file_from_github(access_token, repo, file_path)
                
        #         file.is_deleted = True
        #         file.deleted_at = timezone.now()
        #         for user in users_with_view_permission:
        #             print(user.email)
        #             if request.user != user:
        #                 Notification.objects.create(
        #                     user=user,
        #                     message=f"A file - {file_name} has been deleted from directory {directory_name}"
        #                 )
        #                 print(user.email)
        #                 send_mail('A file was deleted in your project', f"A file - {file_name} has been deleted from directory {directory_name}", settings.EMAIL_USER, [user.email])
        #     except Exception as e:
        #         return HttpResponse(f"An error occurred while deleting the file from GitHub: {e}", status=500)

        
        

    return HttpResponse("Invalid request method.", status=405)

@login_required
def project_code(request, pk):
    project = get_object_or_404(Project, pk=pk, is_deleted=False)
    
    if request.user != project.manager:
        directories_with_view_permissions = Directory.objects.filter(
            project=project,
            view_permissions=request.user,
            is_deleted=False
        )
        code_files = File.objects.filter(
            project=project,
            file_type='code',
            directory__in=directories_with_view_permissions,
            is_deleted=False
        )
    else:
        directories_with_view_permissions = Directory.objects.filter(
            project=project,
            is_deleted=False
        )
        code_files = File.objects.filter(
            project=project,
            file_type='code',
            is_deleted=False
        )
        
    if request.method == 'POST':
        form = CodeFileForm(request.POST, request.FILES, project=project, user=request.user)
        if form.is_valid():
            file = form.save(commit=False)
            file.project = project
            file.directory = form.cleaned_data['directory']
            file.file_type = 'code'
            file.save()
            users_with_view_permission = file.directory.view_permissions.all()
            try:
                access_token = settings.GITHUB_TOKEN
                if not access_token:
                    raise ValueError("GitHub access token is not configured.")
                
                directory_path = get_directory_path(file.directory)
                filename = file.file.name[6:]

                file_content = file.file.read()
                upload_file_to_github(
                    access_token,
                    f"{project.name}{project.id}/{directory_path}/{filename}",
                    file_content,
                    "File upload"
                )
                for user in users_with_view_permission:
                    # Send notification only if the user is not the current one
                    if request.user != user:
                        Notification.objects.create(
                                user=user,
                                message=f"A file - {filename} has been uploaded to directory {file.directory.name}"
                            )
                        send_mail('A file was uploaded to your project', f"A file - {filename} has been uploaded to directory {file.directory.name}", settings.EMAIL_USER, [user.email])

            except ValueError as e:
                return HttpResponse(f"Error: {e}", status=400)
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}", status=500)

            return redirect('project_code', pk=project.id)
    else:
        form = CodeFileForm(project=project, user=request.user)

    return render(request, 'users/project_code.html', {
        'project': project,
        'form': form,
        'code_files': code_files,
        'directories': directories_with_view_permissions,
    })
    
@login_required
def developer_home(request):
    if request.user.persona != 'developer':
        return redirect('home')
    
    user = request.user
    projects = Project.objects.filter(team_members=user, is_deleted=False)
    return render(request, 'users/developer_home.html', {'projects': projects})

@login_required
def manager_home(request):
    if request.user.persona != 'manager':
        return redirect('home')

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.manager = request.user
            project.save()
            emails = form.cleaned_data['team_member_emails'].split(',')
            for email in emails:
                email = email.strip()
                send_invitation_email(request, email, project.id)
            return redirect('manager_home')
    else:
        form = ProjectForm()

    projects = Project.objects.filter(manager=request.user, is_deleted=False)
    
    # מציאת משתמשים שמקושרים לפרויקטים שהמנהל מנהל
    shared_project_users = User.objects.filter(
        projects__manager=request.user
    ).distinct()

    return render(request, 'users/manager_home.html', {
        'form': form,
        'projects': projects,
        'shared_project_users': shared_project_users
    })

@login_required
def send_invitation_email(request, email, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Create an Invitation object
    invitation = Invitation(email=email, project=project)
    invitation.save()
    
    # Send email
    accept_url = request.build_absolute_uri(reverse('accept_invitation', args=[invitation.id]))
    email_subject = f"Invitation to join project {project.name}"
    email_body = f"Hi,\n\nYou have been invited to join the project '{project.name}'.\n\nPlease click the link below to accept the invitation:\n{accept_url}\n\nBest regards,\nProject Management Team"
    send_mail(email_subject, email_body, settings.EMAIL_USER, [invitation.email])

def accept_invitation(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    user = request.user
    
    if user.is_authenticated and user.persona == "developer":
        if not invitation.project.team_members.filter(id=user.id).exists():
            invitation.project.team_members.add(user)
        
        project_id = invitation.project.id
        invitation.delete()
        return redirect('project_detail', pk=project_id)
    else:
        # User is not logged in, redirect to login page
        login_url = f"{reverse('login')}?next={reverse('accept_invitation', args=[invitation.id])}"
        return redirect(login_url)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is verified
            user.verification_code = uuid.uuid4()
            user.save()
            logger.debug(f"Generated verification code during registration: {user.verification_code} for user: {user.username}")
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('users/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'token': str(user.verification_code),  # Convert to string
            })
            send_mail(mail_subject, message, settings.EMAIL_USER, [user.email])
            return redirect('email_verification')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def email_verification(request):
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            logger.debug(f"Submitted verification code: {code}")
            try:
                user = User.objects.get(verification_code=uuid.UUID(code))  # Convert to UUID
                logger.debug(f"Retrieved user: {user.username} with verification code: {user.verification_code}")
                if user and not user.is_verified:
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    login(request, user)
                    return redirect('home')
            except (User.DoesNotExist, ValueError):
                logger.debug(f"User does not exist for the provided verification code: {code}")
                pass
        return render(request, 'users/email_verification.html', {'form': form, 'error': 'Invalid verification code'})
    else:
        form = VerificationForm()
    return render(request, 'users/email_verification.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_verified and not user.blocked:
                # Generate a new verification code
                user.verification_code = uuid.uuid4()
                user.save()

                # Send the verification code to the user’s email
                mail_subject = 'Your login verification code'
                message = f'Your verification code is {user.verification_code}'
                send_mail(mail_subject, message, settings.EMAIL_USER, [user.email])

                request.session['user_id'] = user.id  # Store user ID in session
                return redirect('verify_code')  # Redirect to code verification page
            elif user is not None and user.blocked:
                return render(request, 'users/login.html', {'form': form, 'error': 'Your account has been blocked by an admin'})
            else:
                return render(request, 'users/login.html', {'form': form, 'error': 'Invalid username/password or account not verified'})
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def verify_code(request):
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            user_id = request.session.get('user_id')
            try:
                user = User.objects.get(id=user_id, verification_code=code)
                if user and not user.blocked:
                    login(request, user)  # Log the user in
                    return redirect('home')
            except User.DoesNotExist:
                pass
        return render(request, 'users/email_verification.html', {'form': form, 'error': 'Invalid verification code'})
    else:
        form = VerificationForm()
    
    return render(request, 'users/email_verification.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, is_deleted=False)
    user = request.user

    if user != project.manager and not project.team_members.filter(id=user.id).exists():
        raise PermissionDenied

    if request.method == 'POST':
        if user == project.manager:
            new_description = request.POST.get('description', '')
            project.description = new_description
            project.save()
            messages.success(request, "Project description updated successfully.")
            return redirect('project_detail', pk=pk)
        else:
            return HttpResponseForbidden("You do not have permission to edit this project.")

    return render(request, 'users/project_detail.html', {'project': project})

def project_settings(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.manager != request.user:
        raise PermissionDenied

    # get users who have worked with this manager on other projects
    shared_project_users = User.objects.filter(
        projects__manager=request.user
    ).distinct()
    return render(request, 'users/project_settings.html', {
        'project': project,
        'shared_project_users': shared_project_users
    })
    
@login_required
def invite_member(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.manager != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        email = request.POST.get('manual_email') or request.POST.get('suggested_email')
        if not email:
            messages.error(request, 'Please select a team member or enter an email address.')
            return redirect('project_settings', pk=project_id)
        user = User.objects.filter(email=email).first()
        if user:
            if project.team_members.filter(id=user.id).exists():
                messages.warning(request, f'{user.username} is already a member of the project.')
            else:
                send_invitation_email(request, email, project.id)
                messages.success(request, f'{user.username} has been invited to the project.')
        else:
            # Handle the case where the email is not associated with an existing user
            messages.info(request, f'An invitation email has been sent to {email}.')

    return redirect('project_settings', pk=project_id)

from .forms import TaskForm



@login_required
def create_task(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.project = project  # שיוך המשימה לפרויקט הנוכחי
            task.save()
            form.save_m2m()

            messages.success(request, 'Task created successfully and assigned to the selected developers.')

            form = TaskForm(user=request.user)  # טופס חדש וריק לאחר יצירת המשימה
    else:
        form = TaskForm(user=request.user)

    return render(request, 'users/create_task.html', {'form': form, 'project': project})

@login_required
def developer_tasks(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        task = Task.objects.get(id=task_id, assigned_to=request.user)
        task.is_done = True
        task.save()

        # שליחת מייל למנהל הפרויקט
        send_mail(
            'Task Completed',
            f'The task "{task.title}" has been marked as done by {request.user.username}.',
            settings.EMAIL_USER,
            [task.created_by.email],
            fail_silently=False,
        )

        # הצגת הודעה למשתמש
        messages.success(request, 'Task marked as done successfully. An email has been sent to the project manager.')

        return redirect('developer_tasks')  # הפניה חזרה לרשימת המשימות

    # שליפת כל המשימות שהוקצו למשתמש המחובר
    tasks = Task.objects.filter(assigned_to=request.user)
    return render(request, 'users/developer_tasks.html', {'tasks': tasks})


@login_required
def mark_task_done(request, task_id):
    task = Task.objects.get(pk=task_id)
    if request.user in task.assigned_to.all():
        task.is_done = True
        task.save()

        # Send email to the manager
        send_mail(
            'Task Completed',
            f'The task "{task.title}" has been marked as done by {request.user.username}.',
            settings.EMAIL_USER,
            [task.created_by.email]
        )

        return redirect('task_list')
    return redirect('task_list')

@login_required
def project_tasks(request, project_id):
    project = get_object_or_404(Project, pk=project_id, is_deleted=False)
    if request.user != project.manager:
        raise PermissionDenied
    tasks = Task.objects.filter(project=project, created_by=request.user)

    return render(request, 'users/project_tasks.html', {
        'project': project,
        'tasks': tasks,
    })

# יצירת לוגים
logger = logging.getLogger(__name__)

@login_required
def ai_code_improvement(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    gpt_response = None
    action = None
    if request.method == 'POST':
        code = request.POST.get('code')
        action = request.POST.get('action')
        logger.debug(f"Code submitted: {code}")
        if code:
            try:
                openai.api_key = settings.OPENAI_API_KEY
                if action == 'improve':
                    prompt = f"Please review and improve the following code:\n{code}"
                elif action == 'optimize':
                    prompt = f"Please optimize the following code for better performance:\n{code}"
                elif action == 'find_bugs':
                    prompt = f"Please find and fix potential bugs in the following code:\n{code}"
                elif action == 'refactor':
                    prompt = f"Please refactor the following code for better readability and maintainability:\n{code}"
                elif action == 'add_comments':
                    prompt = f"Please add comments to the following code:\n{code}"
                elif action == 'describe':
                    prompt = f"Please describe the following code:\n{code}"
                # Call the OpenAI API using the correct method
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )

                # הדפסת התגובה ל-console
                logger.debug(f"Response from OpenAI: {response}")

                # בדיקת תוכן התגובה
                if response and response.choices:
                    gpt_response = response.choices[0].message.content
                    logger.debug(f"Suggestions: {gpt_response}")
                else:
                    messages.error(request, "No suggestions were returned by the AI.")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                logger.error(f"Error communicating with OpenAI: {e}")
        else:
            messages.error(request, "Please enter some code.")
            logger.debug("No code was entered.")
    
    logger.debug(f"Suggestions to be shown: {gpt_response}")

    return render(request, 'users/ai_code_improvement.html', {
        'project': project,
        'suggestions': gpt_response,
        'action': action
    })
    
@login_required
def mark_notification_as_read(request, notification_id):
    print(f"Marking notification {notification_id} as read")
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    print(f"Notification {notification_id} marked as read")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def mark_all_notifications_as_read(request):
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    unread_notifications.update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'home'))
