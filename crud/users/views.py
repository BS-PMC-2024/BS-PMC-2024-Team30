from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from .models import User, Project, Permission, File, Directory, Invitation
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.http import HttpResponseForbidden
from .forms import CustomUserCreationForm, LoginForm, VerificationForm, InvitationForm
from .forms import ProjectForm, DirectoryForm
from django.http import HttpResponseForbidden, HttpResponse
from .forms import CustomUserCreationForm, LoginForm, VerificationForm
from .forms import ProjectForm, DocumentFileForm, DirectoryForm, CodeFileForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
import uuid
import logging
from .github_service import GitHubService
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from .models import Project


#project delete add"
import requests
import base64



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

    
        
def view_file(request, project_id, file_id):
    project = get_object_or_404(Project, pk=project_id)
    file = get_object_or_404(File, id=file_id)
    access_token = settings.GITHUB_TOKEN
    repo = settings.GITHUB_REPO

    directory_path = get_directory_path(file.directory)
    try:
        file_content = get_file_from_github(access_token, repo, f"{project.name}{project.id}/{directory_path}/{file.file.name}")

        return render(request, 'users/view_file.html', {'file_content': file_content, 'file_name': file.file.name})
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return HttpResponse(f"HTTP error occurred: {http_err}", status=500)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return HttpResponse(f"An unexpected error occurred: {e}", status=500)


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
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        form = DirectoryForm(request.POST, project=project)
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

            except ValueError as e:
                return HttpResponse(f"Error: {e}", status=400)
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}", status=500)

            return redirect('manage_directories', project_id=project.id)
    else:
        form = DirectoryForm(project=project)

    directories = Directory.objects.filter(project=project, parent__isnull=True)
    return render(request, 'users/manage_directories.html', {
        'form': form,
        'directories': directories,
        'project': project,
    })

def view_directory(request, directory_id):
    directory = get_object_or_404(Directory, pk=directory_id)
    
    if directory.project.manager != request.user:
        return HttpResponseForbidden("You do not have permission to view this directory.")

    # Handle file deletion
    if 'delete_file' in request.POST:
        file_id = request.POST.get('file_id')
        if file_id:
            file = get_object_or_404(File, id=file_id)
            if file.directory == directory:
                access_token = settings.GITHUB_TOKEN
                repo = settings.GITHUB_REPO
                directory_path = get_directory_path(file.directory)
                file_path = f"{directory.project.name}/{directory_path}/{file.file.name}"
                try:
                    print("1")
                    delete_file_from_github(access_token, repo, file_path)
                except Exception as e:
                    return HttpResponse(f"An error occurred while deleting the file from GitHub: {e}", status=500)

                file.delete()
            else:
                return HttpResponseForbidden("You do not have permission to delete this file.")
        return redirect('view_directory', directory_id=directory_id)

    breadcrumb = []
    current_directory = directory
    while current_directory:
        breadcrumb.append(current_directory)
        current_directory = current_directory.parent
    breadcrumb.reverse() 

    return render(request, 'users/view_directory.html', {
        'directory': directory,
        'breadcrumb': breadcrumb,
    })


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
        # Delete from GitHub
        delete_directory_from_github(access_token, repo, f"{directory.project.name}/{get_directory_path(directory)}")
        
        # Delete from the database
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

def project_documents(request, pk):
    project = get_object_or_404(Project, pk=pk)
    directories = Directory.objects.filter(project=project)
    document_files = File.objects.filter(project=project, file_type='document')

    if request.method == 'POST':
        form = DocumentFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.project = project
            file.directory = Directory.objects.get(id=request.POST['directory'])
            file.file_type='document'
            file.save()
            try:
                access_token = settings.GITHUB_TOKEN
                if not access_token:
                    raise ValueError("GitHub access token is not configured.")
                
                directory_path = get_directory_path(file.directory)
                print(directory_path)
                filename = file.file.name
                filename = filename[6:]
                print(filename)
                file_content = file.file.read()
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
        'directories': directories,
        'project': project,
        'document_files': document_files,
    })

        
def project_code(request, pk):
    project = get_object_or_404(Project, pk=pk)
    directories = Directory.objects.filter(project=project)
    code_files = File.objects.filter(project=project, file_type='code')
    print("Directories:", directories)
    
    if request.method == 'POST':
        form = CodeFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.project = project
            file.directory = Directory.objects.get(id=request.POST['directory'])
            file.file_type = 'code'
            file.save()
            try:
                access_token = settings.GITHUB_TOKEN
                if not access_token:
                    raise ValueError("GitHub access token is not configured.")
                
                directory_path = get_directory_path(file.directory)
                
                filename = file.file.name
                filename = filename[6:]
                
                file_content = file.file.read()
                upload_file_to_github(
                    access_token,
                    f"{project.name}{project.id}/{directory_path}/{filename}",
                    file_content,
                    "File upload"
                )

            except ValueError as e:
                return HttpResponse(f"Error: {e}", status=400)
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}", status=500)

            return redirect('users/project_code', pk=project.id)
    else:
        form = CodeFileForm()

    return render(request, 'users/project_code.html', {
        'project': project,
        'form': form,
        'code_files': code_files,
        'directories': directories,  # Pass directories to the template
    })
@login_required
def developer_home(request):
    if request.user.persona != 'developer':
        return redirect('home')
    
    user = request.user
    projects = Project.objects.filter(team_members=user)
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
                send_invitation_email(request, email,project.id)
            return redirect('manager_home')
    else:
        form = ProjectForm()

    projects = Project.objects.filter(manager=request.user)

    return render(request, 'users/manager_home.html', {'form': form, 'projects': projects})


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
    send_mail(email_subject, email_body, 'shohamdimri@gmail.com', [invitation.email])

def accept_invitation(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    
    if request.user.is_authenticated:
        invitation.project.team_members.add(request.user)
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
            send_mail(mail_subject, message, 'shohamdimri@gmail.com', [user.email])
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
            
            if user is not None and user.is_verified:
                # Generate a new verification code
                user.verification_code = uuid.uuid4()
                user.save()

                # Send the verification code to the user’s email
                mail_subject = 'Your login verification code'
                message = f'Your verification code is {user.verification_code}'
                send_mail(mail_subject, message, 'shohamdimri@gmail.com', [user.email])

                request.session['user_id'] = user.id  # Store user ID in session
                return redirect('verify_code')  # Redirect to code verification page
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
                if user:
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

@require_http_methods(["POST"])
@login_required
def set_permission(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.manager != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    data = request.POST
    user = User.objects.get(pk=data['user_id'])
    permission_type = data['permission_type']

    Permission.objects.update_or_create(
        user=user,
        project=project,
        defaults={'permission_type': permission_type},
    )
    return JsonResponse({'success': True})

@require_http_methods(["GET"])
@login_required
def get_permissions(request, pk):
    project = get_object_or_404(Project, pk=pk)
    permissions = Permission.objects.filter(project=project)
    permissions_data = [
        {'user': p.user.username, 'permission_type': p.permission_type}
        for p in permissions
    ]
    return JsonResponse(permissions_data, safe=False)

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    user = request.user
    
    if user != project.manager and not project.team_members.filter(id=user.id).exists():
        raise PermissionDenied
    return render(request, 'users/project_detail.html', {'project': project})

def project_settings(request, pk):
    project = get_object_or_404(Project, pk=pk)
    permission = Permission.objects.filter(user=request.user, project=project, permission_type='edit').exists()
    if not permission and project.manager != request.user:
        raise PermissionDenied
    return render(request, 'users/project_settings.html', {'project': project})