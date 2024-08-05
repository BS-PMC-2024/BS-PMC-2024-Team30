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
