import base64
import time
from django.contrib import messages
import shutil
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
import requests
from .models import Project, User  # Adjust the import to point to your custom User model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from .models import Project
from .forms import ProjectForm
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import Project, Directory
#from .forms import DirectoryForm
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from unittest.mock import patch, MagicMock
from .models import Project, Directory, File
from .views import get_directory_path
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from .models import Project, Directory, File
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import Project
from .views import project_detail
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.models import AnonymousUser
from .views import logout_view
import unittest
from unittest.mock import patch, Mock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.http import Http404
from .views import get_file_from_github, delete_file_from_github, download_file, view_file, update_file_on_github
from .models import File, Project

import base64
from django.test import TestCase
import requests
from .views import get_file_from_github, delete_file_from_github

class DeleteProjectTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpassword')
        self.project = Project.objects.create(name='Test Project', manager=self.user)
        self.client.login(username='testuser', password='testpassword')

    def test_delete_project_post(self):
        response = self.client.post(reverse('delete_project', args=[self.project.id]))
        self.assertRedirects(response, reverse('home'), status_code=302, target_status_code=302)
        self.assertFalse(Project.objects.filter(id=self.project.id).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f'Project "{self.project.name}" has been deleted.')

    def test_delete_project_get(self):
        response = self.client.get(reverse('delete_project', args=[self.project.id]))
        self.assertRedirects(response, reverse('project_settings', kwargs={'pk': self.project.id}), status_code=302, target_status_code=200)
        self.assertTrue(Project.objects.filter(id=self.project.id).exists())

    def test_delete_project_not_manager(self):
        other_user = User.objects.create_user(username='otheruser', email='otheruser@example.com', password='otherpassword')
        other_project = Project.objects.create(name='Other Project', manager=other_user)
        response = self.client.post(reverse('delete_project', args=[other_project.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Project.objects.filter(id=other_project.id).exists())

User = get_user_model()

class ManagerHomeTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='password', persona='manager')
        self.developer = User.objects.create_user(username='developer', email='developer@example.com', password='password', persona='developer')
        self.client.login(username='manager', password='password')

    def test_redirect_non_manager(self):
        self.client.login(username='developer', password='password')
        response = self.client.get(reverse('manager_home'))
        self.assertRedirects(response, reverse('home'), status_code=302, target_status_code=302)

    def test_render_manager_home(self):
        response = self.client.get(reverse('manager_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/manager_home.html')
        self.assertIsInstance(response.context['form'], ProjectForm)

    def test_handle_invalid_form(self):
        data = {
            'name': '',  # Invalid name
            'description': 'Project Description',
            'team_member_emails': 'member1@example.com, member2@example.com'
        }
        response = self.client.post(reverse('manager_home'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/manager_home.html')
        self.assertFalse(Project.objects.filter(description='Project Description').exists())
        self.assertIsInstance(response.context['form'], ProjectForm)
        self.assertTrue(response.context['form'].errors)

    def test_invite_recommendations(self):
        url = reverse('manager_home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/manager_home.html')
        self.assertIsInstance(response.context['form'], ProjectForm)
        self.assertQuerysetEqual(response.context['projects'], Project.objects.filter(manager=self.manager))
        self.assertQuerysetEqual(response.context['shared_project_users'], User.objects.filter(projects__manager=self.manager).distinct())


User = get_user_model()

class DeleteDirectoryTestCase(TestCase):

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='password', persona='manager')
        self.developer = User.objects.create_user(username='developer', email='developer@example.com', password='password', persona='developer')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)
        self.sub_directory = Directory.objects.create(name='Sub Directory', project=self.project, parent=self.directory)
        self.file = File.objects.create(file='test_file.txt', directory=self.sub_directory, project=self.project)
        self.client.login(username='manager', password='password')

    # @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    # @patch('users.views.delete_directory_from_github')
    # def test_delete_directory_as_manager(self, mock_delete_from_github):
    #     response = self.client.post(reverse('delete_directory', args=[self.directory.id]))
    #     self.assertRedirects(response, reverse('project_code', args=[self.project.id]))
    #     mock_delete_from_github.assert_called_once_with('fake_token', 'fake_repo', f"{self.project.name}/{self.directory.name}")
    #     self.assertFalse(Directory.objects.filter(id=self.directory.id).exists())

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    def test_delete_directory_as_non_manager(self):
        self.client.login(username='developer', password='password')
        response = self.client.post(reverse('delete_directory', args=[self.directory.id]))
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission to delete this directory.", response.content.decode())

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    @patch('users.views.delete_directory_from_github')
    def test_delete_directory_github_error(self, mock_delete_from_github):
        mock_delete_from_github.side_effect = Exception("GitHub error")
        response = self.client.post(reverse('delete_directory', args=[self.directory.id]))
        self.assertEqual(response.status_code, 500)
        self.assertIn("An error occurred: GitHub error", response.content.decode())
        self.assertTrue(Directory.objects.filter(id=self.directory.id).exists())

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    def test_delete_directory_not_found(self):
        response = self.client.post(reverse('delete_directory', args=[999]))  # Non-existent directory ID
        self.assertEqual(response.status_code, 404)

    # @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    # @patch('users.views.delete_directory_from_github')
    # def test_delete_subdirectory_and_files(self, mock_delete_from_github):
    #     response = self.client.post(reverse('delete_directory', args=[self.sub_directory.id]))
    #     self.assertRedirects(response, reverse('project_code', args=[self.project.id]))
    #     self.assertFalse(Directory.objects.filter(id=self.sub_directory.id).exists())
    #     self.assertFalse(File.objects.filter(id=self.file.id).exists())
    #     mock_delete_from_github.assert_called_once_with('fake_token', 'fake_repo', f"{self.project.name}/{self.directory.name}/{self.sub_directory.name}")



User = get_user_model()

class ProjectDetailViewTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.manager = User.objects.create_user(
            username='manageruser',
            email='manager@example.com',
            password='password123',
            persona='manager'
        )
        self.team_member = User.objects.create_user(
            username='teamuser',
            email='teamuser@example.com',
            password='password123',
            persona='developer'
        )
        self.non_member = User.objects.create_user(
            username='nonmember',
            email='nonmember@example.com',
            password='password123',
            persona='developer'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            manager=self.manager
        )
        self.project.team_members.add(self.team_member)

    def test_project_detail_as_manager(self):
        request = self.factory.get(reverse('project_detail', args=[self.project.pk]))
        request.user = self.manager
        response = project_detail(request, self.project.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

    def test_project_detail_as_team_member(self):
        request = self.factory.get(reverse('project_detail', args=[self.project.pk]))
        request.user = self.team_member
        response = project_detail(request, self.project.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

    def test_project_detail_as_non_member(self):
        request = self.factory.get(reverse('project_detail', args=[self.project.pk]))
        request.user = self.non_member
        with self.assertRaises(PermissionDenied):
            project_detail(request, self.project.pk)
             
    def test_update_description_by_manager(self):
        self.client.login(username='manageruser', password='password123')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})

        response = self.client.post(url, {'description': 'Updated Description'})

        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, 'Updated Description')
        self.assertTrue(messages.get_messages(response.wsgi_request))

    def test_update_description_by_non_manager(self):
        self.client.login(username='teamuser', password='password123')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})

        response = self.client.post(url, {'description': 'Should Not Update'})
        
        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, 'A test project')
        self.assertFalse(messages.get_messages(response.wsgi_request))


User = get_user_model()

class LogoutViewTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )

    def test_logout_view(self):
        request = self.factory.get(reverse('logout'))
        request.user = self.user

        # Adding session to the request
        self.client.login(username='testuser', password='password123')
        request.session = self.client.session

        response = logout_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertIsInstance(request.user, AnonymousUser)



class GitHubAPITests(TestCase):
    def setUp(self):
        self.access_token = 'fake_token'
        self.repo = 'fake_repo'
        self.file_path = 'fake_file_path'

    @patch('users.views.requests.get')
    def test_get_file_from_github_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': base64.b64encode('file content'.encode()).decode()
        }
        mock_get.return_value = mock_response

        content = get_file_from_github(self.access_token, self.repo, self.file_path)
        self.assertEqual(content, 'file content')

    @patch('users.views.requests.get')
    def test_get_file_from_github_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            get_file_from_github(self.access_token, self.repo, self.file_path)

    @patch('users.views.requests.delete')
    @patch('users.views.get_sha_of_path', return_value='fake_sha')
    def test_delete_file_from_github_success(self, mock_get_sha, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        delete_file_from_github(self.access_token, self.repo, self.file_path)
        mock_delete.assert_called_once()

    @patch('users.views.requests.delete')
    @patch('users.views.get_sha_of_path', return_value=None)
    def test_delete_file_from_github_file_not_found(self, mock_get_sha, mock_delete):
        delete_file_from_github(self.access_token, self.repo, self.file_path)
        mock_delete.assert_not_called()

#if __name__ == '__main__':
 #   unittest.main()

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from django.http import Http404
from unittest.mock import patch, Mock
import os

from users.models import User, Project, Directory, File
from users.views import download_file

class DownloadFileTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass')
        self.project = Project.objects.create(name='Test Project', manager=self.user)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)
        self.file = File.objects.create(project=self.project, directory=self.directory, file='files/test_file.txt')
        self.file_path = self.file.file.path
        self.download_url = reverse('download_file', args=[self.project.pk, self.file.id])

        if not os.path.exists('files'):
            os.makedirs('files')
        with open(self.file_path, 'w') as f:
            f.write('Dummy content')

    def tearDown(self):
        if os.path.exists('files'):
            for root, dirs, files in os.walk('files'):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.delete_file_with_retries(file_path)
            shutil.rmtree('files', ignore_errors=True)

    def delete_file_with_retries(self, file_path):
        retries = 5
        for i in range(retries):
            try:
                os.remove(file_path)
                break
            except PermissionError:
                time.sleep(0.2)

    # @patch('users.views.get_object_or_404')
    # def test_download_file_success(self, mock_get_object_or_404):
    #     mock_get_object_or_404.side_effect = [self.file, self.project]

    #     request = self.factory.get(self.download_url)
    #     request.user = self.user

    #     response = download_file(request, self.project.pk, self.file.id)

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response['Content-Disposition'], f'attachment; filename="{os.path.basename(self.file_path)}"')

    # @patch('users.views.get_object_or_404')
#     def test_download_file_not_found(self, mock_get_object_or_404):
#         mock_get_object_or_404.side_effect = [self.file, self.project]

#         request = self.factory.get(self.download_url)
#         request.user = self.user

#         os.remove(self.file_path)  # Ensure the file does not exist

#         with self.assertRaises(Http404):
#             download_file(request, self.project.pk, self.file.id)

# if __name__ == '__main__':
#     import unittest
#     unittest.main()

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.conf import settings
from django.http import Http404
from unittest.mock import patch, Mock
import os
import requests

from users.models import User, Project, Directory, File
from users.views import view_file, get_file_from_github, delete_file_from_github, download_file

class ViewFileTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpass')
        self.project = Project.objects.create(name='Test Project', manager=self.user)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)
        self.file = File.objects.create(project=self.project, directory=self.directory, file='files/test_file.txt')
        self.view_url = reverse('view_file', args=[self.project.pk, self.file.id])

        if not os.path.exists('files'):
            os.makedirs('files')
        with open(self.file.file.path, 'w') as f:
            f.write('Dummy content')

    def tearDown(self):
        if os.path.exists('files'):
            for root, dirs, files in os.walk('files'):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.delete_file_with_retries(file_path)
            shutil.rmtree('files', ignore_errors=True)

    def delete_file_with_retries(self, file_path):
        retries = 5
        for i in range(retries):
            try:
                os.remove(file_path)
                break
            except PermissionError:
                time.sleep(0.2)
    # @patch('users.views.get_file_from_github')
    # @patch('users.views.get_object_or_404')
    # def test_view_file_success(self, mock_get_object_or_404, mock_get_file_from_github):
    #     mock_get_object_or_404.side_effect = lambda model, **kwargs: self.file if model == File else self.project
    #     mock_get_file_from_github.return_value = 'File content from GitHub'

    #     request = self.factory.get(self.view_url)
    #     request.user = self.project.manager

    #     response = view_file(request, self.project.pk, self.file.id)

    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'File content from GitHub')
    #     self.assertContains(response, 'test_file.txt')

#     @patch('users.views.get_file_from_github')
#     @patch('users.views.get_object_or_404')
#     def test_view_file_github_error(self, mock_get_object_or_404, mock_get_file_from_github):
#         mock_get_object_or_404.side_effect = lambda model, **kwargs: self.file if model == File else self.project
#         mock_get_file_from_github.side_effect = requests.exceptions.HTTPError("GitHub error")

#         request = self.factory.get(self.view_url)
#         request.user = self.project.manager

#         response = view_file(request, self.project.pk, self.file.id)

#         self.assertEqual(response.status_code, 500)
#         self.assertContains(response, 'HTTP error occurred: GitHub error', status_code=500)

# if __name__ == '__main__':
#     import unittest
#     unittest.main()

from django.test import TestCase
from unittest.mock import patch, Mock, ANY
import requests
from users.views import update_file_on_github

class UpdateFileOnGitHubTests(TestCase):
    @patch('users.views.requests.put')
    @patch('users.views.requests.get')
    def test_update_file_on_github_success(self, mock_get, mock_put):
        mock_get.return_value.json.return_value = {'sha': 'fake_sha'}
        mock_get.return_value.status_code = 200
        mock_put.return_value.status_code = 200

        access_token = 'fake_token'
        repo = 'fake_repo'
        path = 'fake_path'
        content = 'new content'

        update_file_on_github(access_token, repo, path, content)

        mock_get.assert_called_once_with(
            f'https://api.github.com/repos/{repo}/contents/{path}',
            headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
        )

        mock_put.assert_called_once_with(
            f'https://api.github.com/repos/{repo}/contents/{path}',
            headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            json={
                'message': 'Update file content',
                'content': ANY,  # Use ANY here
                'sha': 'fake_sha'
            }
        )

    @patch('users.views.requests.put')
    @patch('users.views.requests.get')
    def test_update_file_on_github_error(self, mock_get, mock_put):
        mock_get.return_value.json.return_value = {'sha': 'fake_sha'}
        mock_get.return_value.status_code = 200
        mock_put.side_effect = requests.exceptions.HTTPError("GitHub error")

        access_token = 'fake_token'
        repo = 'fake_repo'
        path = 'fake_path'
        content = 'new content'

        with self.assertRaises(requests.exceptions.HTTPError):
            update_file_on_github(access_token, repo, path, content)

        mock_get.assert_called_once_with(
            f'https://api.github.com/repos/{repo}/contents/{path}',
            headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
        )

        mock_put.assert_called_once_with(
            f'https://api.github.com/repos/{repo}/contents/{path}',
            headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            json={
                'message': 'Update file content',
                'content': ANY,  # Use ANY here
                'sha': 'fake_sha'
            }
        )

if __name__ == '__main__':
    import unittest
    unittest.main()

from django.test import TestCase
from unittest.mock import patch, Mock
import requests
from users.views import upload_file_to_github
import base64

#class UploadFileToGitHubTests(TestCase):

#     @patch('users.views.requests.put')
#     def test_upload_file_to_github_success(self, mock_put):
#         mock_put.return_value.json.return_value = {'content': 'fake_content'}
#         mock_put.return_value.status_code = 201
        
#         access_token = 'fake_token'
#         path = 'fake_path'
#         content = 'new content'
#         message = 'Initial commit'

#         result = upload_file_to_github(access_token, path, content, message)
#         encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

#         mock_put.assert_called_once_with(
#             f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/{path}",
#             headers={
#                 "Authorization": f"token {access_token}",
#                 "Accept": "application/vnd.github.v3+json"
#             },
#             json={
#                 "message": message,
#                 "content": encoded_content
#             }
#         )

#         self.assertEqual(result, {'content': 'fake_content'})

#     @patch('users.views.requests.put')
#     def test_upload_file_to_github_error(self, mock_put):
#         mock_put.side_effect = requests.exceptions.HTTPError("GitHub error")

#         access_token = 'fake_token'
#         path = 'fake_path'
#         content = 'new content'
#         message = 'Initial commit'

#         with self.assertRaises(requests.exceptions.HTTPError):
#             upload_file_to_github(access_token, path, content, message)
        
#         encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

#         mock_put.assert_called_once_with(
#             f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/{path}",
#             headers={
#                 "Authorization": f"token {access_token}",
#                 "Accept": "application/vnd.github.v3+json"
#             },
#             json={
#                 "message": message,
#                 "content": encoded_content
#             }
#         )

# if __name__ == '__main__':
#     import unittest
#     unittest.main()
from django.test import TestCase
from unittest.mock import patch
from users.views import create_directory_on_github

class CreateDirectoryOnGitHubTests(TestCase):

    @patch('users.views.upload_file_to_github')
    def test_create_directory_on_github_success(self, mock_upload):
        mock_upload.return_value = {'content': 'fake_content'}
        
        access_token = 'fake_token'
        dir_path = 'fake_dir_path'

        result = create_directory_on_github(access_token, dir_path)

        file_path = f"{dir_path}/README.md"
        mock_upload.assert_called_once_with(
            access_token, file_path, "this is a directory.", "create directory"
        )

        self.assertEqual(result, {'content': 'fake_content'})

    @patch('users.views.upload_file_to_github')
    def test_create_directory_on_github_error(self, mock_upload):
        mock_upload.side_effect = requests.exceptions.HTTPError("GitHub error")

        access_token = 'fake_token'
        dir_path = 'fake_dir_path'

        with self.assertRaises(requests.exceptions.HTTPError):
            create_directory_on_github(access_token, dir_path)

        file_path = f"{dir_path}/README.md"
        mock_upload.assert_called_once_with(
            access_token, file_path, "this is a directory.", "create directory"
        )

if __name__ == '__main__':
    import unittest
    unittest.main()
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth import get_user_model
from users.models import Project, Directory

User = get_user_model()

class ManageDirectoriesTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.project = Project.objects.create(name='Test Project', manager=self.user)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)
        self.url = reverse('manage_directories', args=[self.project.id])
        self.client.login(username='testuser', password='12345')

    # @patch('users.views.create_directory_on_github')
    # @patch('users.views.DirectoryManagementForm')
    # def test_manage_directories_post_valid(self, mock_form_class, mock_create_directory):
    #     mock_form = mock_form_class.return_value
    #     mock_form.is_valid.return_value = True
    #     mock_form.cleaned_data = {
    #         'view_permissions': [self.user],
    #         'edit_permissions': [self.user],
    #     }
    #     mock_form.save.return_value = self.directory

    #     response = self.client.post(self.url, {'name': 'New Directory'})

    #     self.assertEqual(response.status_code, 302)
    #     self.assertEqual(response.url, self.url)
    #     mock_create_directory.assert_called_once()
    #     self.directory.refresh_from_db()
    #     self.assertTrue(self.directory.view_permissions.filter(id=self.user.id).exists())
    #     self.assertTrue(self.directory.edit_permissions.filter(id=self.user.id).exists())

    # @patch('users.views.DirectoryManagementForm')
    # def test_manage_directories_post_invalid_form(self, mock_form_class):
    #     mock_form = mock_form_class.return_value
    #     mock_form.is_valid.return_value = False

    #     response = self.client.post(self.url, {'name': 'New Directory'})

    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'users/manage_directories.html')
    #     self.assertFalse(Directory.objects.filter(name='New Directory').exists())

#     @patch('users.views.create_directory_on_github')
#     @patch('users.views.DirectoryManagementForm')
#     def test_manage_directories_github_error(self, mock_form_class, mock_create_directory):
#         mock_form = mock_form_class.return_value
#         mock_form.is_valid.return_value = True
#         mock_form.cleaned_data = {
#             'view_permissions': [self.user],
#             'edit_permissions': [self.user],
#         }
#         mock_form.save.return_value = self.directory
#         mock_create_directory.side_effect = Exception("GitHub error")

#         response = self.client.post(self.url, {'name': 'New Directory'})

#         self.assertEqual(response.status_code, 500)
#         self.assertIn(b'An error occurred: GitHub error', response.content)

# if __name__ == '__main__':
#     import unittest
#     unittest.main()

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from users.models import Project, Directory
from django.test import RequestFactory

class ViewDirectoryTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='user', password='password', email='user@example.com')
        self.manager = User.objects.create_user(username='manager', password='password', email='manager@example.com')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)
    
    def test_view_directory_as_non_manager(self):
        self.client.login(username='user', password='password')
        url = reverse('view_directory', args=[self.directory.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Expecting a 403 Forbidden status code

# Make sure to update or create a new test_views.py file in your users app directory

from django.test import TestCase, Client
from django.urls import reverse
from users.models import Project, Directory, User

class ViewDirectoryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='password', email='user@example.com')
        self.manager = User.objects.create_user(username='manager', password='password', email='manager@example.com')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)

    def test_view_directory_as_manager(self):
        self.client.login(username='manager', password='password')
        url = reverse('view_directory', args=[self.directory.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/view_directory.html')

    def test_view_directory_as_non_manager(self):
        self.client.login(username='user', password='password')
        url = reverse('view_directory', args=[self.directory.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Expecting a 403 Forbidden status code


# users/tests/test_delete_directory.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import Project, Directory, File
from .views import delete_directory_from_database

User = get_user_model()

class DeleteDirectoryTests(TestCase):

    def setUp(self):
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='password')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        
        # Create a directory structure
        self.root_directory = Directory.objects.create(name='Root Directory', project=self.project)
        self.sub_directory1 = Directory.objects.create(name='Sub Directory 1', project=self.project, parent=self.root_directory)
        self.sub_directory2 = Directory.objects.create(name='Sub Directory 2', project=self.project, parent=self.sub_directory1)

        # Create files in the directories
        self.file1 = File.objects.create(project=self.project, directory=self.root_directory, file='files/file1.txt', file_type='document')
        self.file2 = File.objects.create(project=self.project, directory=self.sub_directory1, file='files/file2.txt', file_type='document')
        self.file3 = File.objects.create(project=self.project, directory=self.sub_directory2, file='files/file3.txt', file_type='document')

    def test_delete_directory_and_contents(self):
        delete_directory_from_database(self.root_directory)
        
        # Ensure all directories and files are deleted
        self.assertFalse(Directory.objects.filter(id=self.root_directory.id).exists())
        self.assertFalse(Directory.objects.filter(id=self.sub_directory1.id).exists())
        self.assertFalse(Directory.objects.filter(id=self.sub_directory2.id).exists())
        self.assertFalse(File.objects.filter(id=self.file1.id).exists())
        self.assertFalse(File.objects.filter(id=self.file2.id).exists())
        self.assertFalse(File.objects.filter(id=self.file3.id).exists())

    def test_delete_subdirectory_and_contents(self):
        delete_directory_from_database(self.sub_directory1)
        
        # Ensure the subdirectory and its contents are deleted
        self.assertTrue(Directory.objects.filter(id=self.root_directory.id).exists())
        self.assertFalse(Directory.objects.filter(id=self.sub_directory1.id).exists())
        self.assertFalse(Directory.objects.filter(id=self.sub_directory2.id).exists())
        self.assertTrue(File.objects.filter(id=self.file1.id).exists())
        self.assertFalse(File.objects.filter(id=self.file2.id).exists())
        self.assertFalse(File.objects.filter(id=self.file3.id).exists())

    def test_delete_leaf_directory(self):
        delete_directory_from_database(self.sub_directory2)
        
        # Ensure only the leaf directory and its file are deleted
        self.assertTrue(Directory.objects.filter(id=self.root_directory.id).exists())
        self.assertTrue(Directory.objects.filter(id=self.sub_directory1.id).exists())
        self.assertFalse(Directory.objects.filter(id=self.sub_directory2.id).exists())
        self.assertTrue(File.objects.filter(id=self.file1.id).exists())
        self.assertTrue(File.objects.filter(id=self.file2.id).exists())
        self.assertFalse(File.objects.filter(id=self.file3.id).exists())


# users/tests/test_project_documents.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from users.models import Project, Directory, File
from users.forms import DocumentFileForm
from unittest.mock import patch, Mock
import os

User = get_user_model()

class ProjectDocumentsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='password')
        self.user = User.objects.create_user(username='user', email='user@example.com', password='password')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        self.url = reverse('project_documents', args=[self.project.id])
        self.client.login(username='manager', password='password')

    def test_get_project_documents(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/project_documents.html')
        self.assertIsInstance(response.context['form'], DocumentFileForm)
        self.assertEqual(list(response.context['document_files']), [])

    @patch('users.views.upload_file_to_github')
    @patch('users.views.get_directory_path')
    @patch('users.views.settings')
    def test_post_project_documents_valid_form(self, mock_settings, mock_get_directory_path, mock_upload_file_to_github):
        mock_settings.GITHUB_TOKEN = 'fake_token'
        mock_get_directory_path.return_value = 'project_documents'

        with open('test_document.txt', 'w') as f:
            f.write('Test document content')

        with open('test_document.txt', 'rb') as doc:
            response = self.client.post(self.url, {
                'document_type': 'report',
                'file': doc,
            })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertTrue(File.objects.filter(project=self.project, file_type='document').exists())

        os.remove('test_document.txt')

    @patch('users.views.upload_file_to_github')
    @patch('users.views.get_directory_path')
    @patch('users.views.settings')
    def test_post_project_documents_existing_file(self, mock_settings, mock_get_directory_path, mock_upload_file_to_github):
        mock_settings.GITHUB_TOKEN = 'fake_token'
        mock_get_directory_path.return_value = 'project_documents'

        document_directory = Directory.objects.create(project=self.project, name='project_documents')
        existing_file = File.objects.create(project=self.project, directory=document_directory, file='report.txt', file_type='document')

        with open('test_document.txt', 'w') as f:
            f.write('Test document content')

        with open('test_document.txt', 'rb') as doc:
            response = self.client.post(self.url, {
                'document_type': 'report',
                'file': doc,
            })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertFalse(File.objects.filter(id=existing_file.id).exists())
        self.assertTrue(File.objects.filter(project=self.project, file_type='document').exists())

        os.remove('test_document.txt')

    @patch('users.views.upload_file_to_github')
    @patch('users.views.settings')
    def test_post_project_documents_no_github_token(self, mock_settings, mock_upload_file_to_github):
        mock_settings.GITHUB_TOKEN = ''

        with open('test_document.txt', 'w') as f:
            f.write('Test document content')

        with open('test_document.txt', 'rb') as doc:
            response = self.client.post(self.url, {
                'document_type': 'report',
                'file': doc,
            })

        self.assertEqual(response.status_code, 400)
        self.assertIn('Error: GitHub access token is not configured.', response.content.decode())

        os.remove('test_document.txt')

    @patch('users.views.upload_file_to_github', side_effect=Exception('GitHub error'))
    @patch('users.views.settings')
    def test_post_project_documents_github_error(self, mock_settings, mock_upload_file_to_github):
        mock_settings.GITHUB_TOKEN = 'fake_token'

        with open('test_document.txt', 'w') as f:
            f.write('Test document content')

        with open('test_document.txt', 'rb') as doc:
            response = self.client.post(self.url, {
                'document_type': 'report',
                'file': doc,
            })

        self.assertEqual(response.status_code, 500)
        self.assertIn('An error occurred: GitHub error', response.content.decode())

        os.remove('test_document.txt')

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Project, Invitation

User = get_user_model()

class AcceptInvitationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='password')
        self.developer = User.objects.create_user(username='developer', email='developer@example.com', password='password', persona='developer')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        self.invitation = Invitation.objects.create(project=self.project, email='developer@example.com')
        self.accept_url = reverse('accept_invitation', args=[self.invitation.id])

    def test_accept_invitation_authenticated_developer(self):
        self.client.login(username='developer', password='password')
        response = self.client.get(self.accept_url)
        self.assertRedirects(response, reverse('project_detail', args=[self.project.id]))
        self.assertTrue(self.project.team_members.filter(id=self.developer.id).exists())
        self.assertFalse(Invitation.objects.filter(id=self.invitation.id).exists())

    def test_accept_invitation_authenticated_non_developer(self):
        user = User.objects.create_user(username='user', email='user@example.com', password='password', persona='manager')
        self.client.login(username='user', password='password')
        response = self.client.get(self.accept_url)
        login_url = f"{reverse('login')}?next={self.accept_url}"
        self.assertRedirects(response, login_url)
        self.assertFalse(self.project.team_members.filter(id=user.id).exists())
        self.assertTrue(Invitation.objects.filter(id=self.invitation.id).exists())

    def test_accept_invitation_unauthenticated_user(self):
        response = self.client.get(self.accept_url)
        login_url = f"{reverse('login')}?next={self.accept_url}"
        self.assertRedirects(response, login_url)
        self.assertFalse(self.project.team_members.filter(id=self.developer.id).exists())
        self.assertTrue(Invitation.objects.filter(id=self.invitation.id).exists())

class ProjectDetailTestCase(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(email="mail1@gmail.com",username='manager', password='managerpassword', persona='manager')
        self.team_member = User.objects.create_user(email="mail2@gmail.com",username='team_member', password='teammemberpassword', persona='team_member')
        self.project = Project.objects.create(name='Test Project', description='Initial Description', manager=self.manager)
        self.project.team_members.add(self.team_member)
        self.client = Client()
       
    
    def test_update_description_by_manager(self):
        self.client.login(username='manager', password='managerpassword')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})

        # Submit a POST request to update description
        response = self.client.post(url, {'description': 'Updated Description'})
        
        # Check for a successful redirect
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, 'Updated Description')
        self.assertTrue(messages.get_messages(response.wsgi_request))

    def test_update_description_by_non_manager(self):
        self.client.login(username='team_member', password='teammemberpassword')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})

        # Try to submit a POST request as a team member
        response = self.client.post(url, {'description': 'Should Not Update'})
        
        # Check for a forbidden status code (403) if a non-manager is trying to update the description
        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, 'Initial Description')
        self.assertFalse(messages.get_messages(response.wsgi_request))
    
    def test_view_project_detail(self):
        self.client.login(username='manager', password='managerpassword')
        url = reverse('project_detail', kwargs={'pk': self.project.pk})

        response = self.client.get(url)
        
        self.assertContains(response, 'Initial Description')
        self.assertContains(response, 'Test Project')
        self.assertContains(response, 'Created on:')
        self.assertContains(response, 'Managed by:')

class InviteMemberTests(TestCase):
    def setUp(self):
        # Create a manager and normal user
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='managerpassword')
        self.user = User.objects.create_user(username='normaluser', email='user@example.com', password='userpassword')

        # Create a project with the manager as the project manager
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        
        # Login as manager
        self.client.login(username='manager', password='managerpassword')

    def test_permission_denied_for_non_manager(self):
        # Log in as a normal user (not the project manager)
        self.client.login(username='normaluser', password='userpassword')

        # Attempt to invite a member (should raise PermissionDenied)
        response = self.client.post(reverse('invite_member', args=[self.project.id]), {
            'manual_email': 'newuser@example.com'
        })

        # Verify that the response raises PermissionDenied
        self.assertEqual(response.status_code, 403)  # 403 Forbidden

    def test_invite_without_email(self):
        # Attempt to invite a member without providing an email
        response = self.client.post(reverse('invite_member', args=[self.project.id]), {
            'manual_email': ''
        })

        # Check that the error message is shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Please select a team member or enter an email address.')
        self.assertEqual(response.status_code, 302)  # Should redirect back to project settings

    def test_invite_existing_member(self):
        # Add the user to the project team members
        self.project.team_members.add(self.user)

        # Attempt to invite the same user again
        response = self.client.post(reverse('invite_member', args=[self.project.id]), {
            'manual_email': 'user@example.com'
        })

        # Check that the warning message is shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), f'{self.user.username} is already a member of the project.')
        self.assertEqual(response.status_code, 302)  # Should redirect back to project settings

    def test_invite_non_member_with_valid_email(self):
        # Attempt to invite a valid user who is not already a team member
        response = self.client.post(reverse('invite_member', args=[self.project.id]), {
            'manual_email': 'user@example.com'
        })

        # Check that the success message is shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), f'{self.user.username} has been invited to the project.')
        self.assertEqual(response.status_code, 302)  # Should redirect back to project settings

    def test_invite_non_existent_user(self):
        # Attempt to invite a non-existent user by email
        response = self.client.post(reverse('invite_member', args=[self.project.id]), {
            'manual_email': 'nonexistent@example.com'
        })

        # Check that the info message is shown
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'An invitation email has been sent to nonexistent@example.com.')
        self.assertEqual(response.status_code, 302)  # Should redirect back to project settings