from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
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
from .forms import DirectoryForm
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

    @patch('users.views.send_invitation_email')
    def test_create_project_and_send_invitations(self, mock_send_invitation_email):
        data = {
            'name': 'New Project',
            'description': 'Project Description',
            'team_member_emails': 'member1@example.com, member2@example.com'
        }
        response = self.client.post(reverse('manager_home'), data)
        self.assertRedirects(response, reverse('manager_home'))
        self.assertTrue(Project.objects.filter(name='New Project').exists())
        mock_send_invitation_email.assert_any_call(response.wsgi_request, 'member1@example.com', Project.objects.get(name='New Project').id)
        mock_send_invitation_email.assert_any_call(response.wsgi_request, 'member2@example.com', Project.objects.get(name='New Project').id)

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



User = get_user_model()

class ManageDirectoriesTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='manager', email='manager@example.com', password='password', persona='manager')
        self.project = Project.objects.create(name='Test Project', manager=self.user)
        self.client.login(username='manager', password='password')

    def test_render_manage_directories_page(self):
        response = self.client.get(reverse('manage_directories', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/manage_directories.html')
        self.assertIsInstance(response.context['form'], DirectoryForm)
        self.assertEqual(response.context['project'], self.project)

    @override_settings(GITHUB_TOKEN='fake_token')
    @patch('users.views.create_directory_on_github')
    def test_create_directory(self, mock_create_directory_on_github):
        data = {
            'name': 'New Directory'
        }
        response = self.client.post(reverse('manage_directories', args=[self.project.id]), data)
        
        self.assertRedirects(response, reverse('manage_directories', args=[self.project.id]))
        self.assertTrue(Directory.objects.filter(name='New Directory', project=self.project).exists())
        mock_create_directory_on_github.assert_called_once()

    def test_handle_invalid_form(self):
        data = {
            'name': ''  # Invalid name
        }
        response = self.client.post(reverse('manage_directories', args=[self.project.id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/manage_directories.html')
        self.assertFalse(Directory.objects.filter(name='').exists())
        self.assertIsInstance(response.context['form'], DirectoryForm)
        self.assertTrue(response.context['form'].errors)

    @override_settings(GITHUB_TOKEN='fake_token')
    @patch('users.views.create_directory_on_github')
    def test_github_integration_error(self, mock_create_directory_on_github):
        mock_create_directory_on_github.side_effect = Exception("GitHub error")
        data = {
            'name': 'New Directory'
        }
        response = self.client.post(reverse('manage_directories', args=[self.project.id]), data)
        
        self.assertEqual(response.status_code, 500)
        self.assertIn("An error occurred: GitHub error", response.content.decode())
        self.assertFalse(Directory.objects.filter(name='New Directory').exists())

    @override_settings(GITHUB_TOKEN='')
    def test_github_token_missing(self):
        data = {
            'name': 'New Directory'
        }
        response = self.client.post(reverse('manage_directories', args=[self.project.id]), data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Error: GitHub access token is not configured.", response.content.decode())
        self.assertFalse(Directory.objects.filter(name='New Directory').exists())

User = get_user_model()

class ViewDirectoryTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username='manager', email='manager@example.com', password='password', persona='manager')
        self.developer = User.objects.create_user(username='developer', email='developer@example.com', password='password', persona='developer')
        self.project = Project.objects.create(name='Test Project', manager=self.manager)
        self.directory = Directory.objects.create(name='Test Directory', project=self.project)
        # Ensure that the correct fields are used when creating the File instance
        self.file = File.objects.create(file='test_file.txt', directory=self.directory, project=self.project)
        self.client.login(username='manager', password='password')

    def test_view_directory_as_manager(self):
        response = self.client.get(reverse('view_directory', args=[self.directory.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/view_directory.html')
        self.assertEqual(response.context['directory'], self.directory)
        self.assertEqual(response.context['project'], self.project)

    def test_view_directory_as_non_manager(self):
        self.client.login(username='developer', password='password')
        response = self.client.get(reverse('view_directory', args=[self.directory.id]))
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission to view this directory.", response.content.decode())

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    @patch('users.views.delete_file_from_github')
    def test_delete_file(self, mock_delete_file_from_github):
        data = {
            'delete_file': '1',
            'file_id': self.file.id
        }
        response = self.client.post(reverse('view_directory', args=[self.directory.id]), data)
        self.assertRedirects(response, reverse('view_directory', args=[self.directory.id]))
        self.assertFalse(File.objects.filter(id=self.file.id).exists())
        mock_delete_file_from_github.assert_called_once()

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    @patch('users.views.delete_file_from_github')
    def test_delete_file_github_error(self, mock_delete_file_from_github):
        mock_delete_file_from_github.side_effect = Exception("GitHub error")
        data = {
            'delete_file': '1',
            'file_id': self.file.id
        }
        response = self.client.post(reverse('view_directory', args=[self.directory.id]), data)
        self.assertEqual(response.status_code, 500)
        self.assertIn("An error occurred while deleting the file from GitHub: GitHub error", response.content.decode())
        self.assertTrue(File.objects.filter(id=self.file.id).exists())

    def test_delete_file_not_found(self):
        data = {
            'delete_file': '1',
            'file_id': 999  # Non-existent file ID
        }
        response = self.client.post(reverse('view_directory', args=[self.directory.id]), data)
        self.assertEqual(response.status_code, 404)

    def test_delete_file_no_permission(self):
        other_directory = Directory.objects.create(name='Other Directory', project=self.project)
        other_file = File.objects.create(file='other_file.txt', directory=other_directory, project=self.project)
        data = {
            'delete_file': '1',
            'file_id': other_file.id
        }
        response = self.client.post(reverse('view_directory', args=[self.directory.id]), data)
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission to delete this file.", response.content.decode())
        self.assertTrue(File.objects.filter(id=other_file.id).exists())

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

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    @patch('users.views.delete_directory_from_github')
    def test_delete_directory_as_manager(self, mock_delete_from_github):
        response = self.client.post(reverse('delete_directory', args=[self.directory.id]))
        self.assertRedirects(response, reverse('project_code', args=[self.project.id]))
        mock_delete_from_github.assert_called_once_with('fake_token', 'fake_repo', f"{self.project.name}/{self.directory.name}")
        self.assertFalse(Directory.objects.filter(id=self.directory.id).exists())

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

    @override_settings(GITHUB_TOKEN='fake_token', GITHUB_REPO='fake_repo')
    @patch('users.views.delete_directory_from_github')
    def test_delete_subdirectory_and_files(self, mock_delete_from_github):
        response = self.client.post(reverse('delete_directory', args=[self.sub_directory.id]))
        self.assertRedirects(response, reverse('project_code', args=[self.project.id]))
        self.assertFalse(Directory.objects.filter(id=self.sub_directory.id).exists())
        self.assertFalse(File.objects.filter(id=self.file.id).exists())
        mock_delete_from_github.assert_called_once_with('fake_token', 'fake_repo', f"{self.project.name}/{self.directory.name}/{self.sub_directory.name}")



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
