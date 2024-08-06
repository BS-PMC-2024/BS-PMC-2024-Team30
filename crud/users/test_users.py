from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch, Mock
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model
from .views import login_view, email_verification, register
import uuid

User = get_user_model()

class SimpleUserTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.verify_code_url = reverse('verify_code')
        self.home_url = reverse('home')
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
            'persona': 'developer'
        }
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Testpass123!'
        )
        self.user.is_verified = False
        self.user.verification_code = uuid.uuid4()
        self.user.save()

    def _add_session_to_request(self, request):
        """Helper method to add session to the request."""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

    @patch('users.views.authenticate')
    @patch('users.views.send_mail')
    def test_login_view_post_valid(self, mock_send_mail, mock_authenticate):
        mock_user = self.user
        mock_user.is_verified = True
        mock_authenticate.return_value = mock_user

        request = self.factory.post(self.login_url, {
            'username': 'testuser',
            'password': 'Testpass123!',
        })
        self._add_session_to_request(request)

        response = login_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.verify_code_url)
        mock_send_mail.assert_called_once()
        mock_user.refresh_from_db()
        self.assertTrue(mock_user.verification_code is not None)

    @patch('users.views.authenticate')
    def test_login_view_post_invalid(self, mock_authenticate):
        mock_authenticate.return_value = None

        request = self.factory.post(self.login_url, {
            'username': 'wronguser',
            'password': 'wrongpassword',
        })
        self._add_session_to_request(request)

        response = login_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username/password or account not verified')

    @patch('users.views.authenticate')
    def test_login_view_unverified_user(self, mock_authenticate):
        mock_user = self.user
        mock_user.is_verified = False
        mock_authenticate.return_value = mock_user

        request = self.factory.post(self.login_url, {
            'username': 'testuser',
            'password': 'Testpass123!',
        })
        self._add_session_to_request(request)

        response = login_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username/password or account not verified')

    @patch('users.views.VerificationForm')
    def test_email_verification_view_post_valid(self, mock_form_class):
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {'code': str(self.user.verification_code)}

        request = self.factory.post(self.verify_code_url, {'code': str(self.user.verification_code)})
        self._add_session_to_request(request)

        response = email_verification(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.home_url)

    @patch('users.views.VerificationForm')
    def test_email_verification_view_post_invalid(self, mock_form_class):
        mock_form = mock_form_class.return_value
        mock_form.is_valid.return_value = False

        request = self.factory.post(self.verify_code_url, {'code': 'invalid_code'})
        self._add_session_to_request(request)

        response = email_verification(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid verification code')

#@patch('users.views.CustomUserCreationForm')
#@patch('users.views.get_current_site')
#@patch('users.views.send_mail')
# def test_register_view_post_valid(self, mock_send_mail, mock_get_current_site, mock_form_class):
#         mock_form = mock_form_class.return_value
#         mock_form.is_valid.return_value = True
#         mock_user = Mock()
#         mock_form.save.return_value = mock_user
#         mock_get_current_site.return_value.domain = 'test.com'

#         request = self.factory.post(self.register_url, self.user_data)
#         self._add_session_to_request(request)

#         response = register(request)
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, self.email_verification_url)
#         mock_send_mail.assert_called_once()
#         mock_user.save.assert_called_once()
