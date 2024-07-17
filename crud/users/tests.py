from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.login_url = reverse('login')  # Make sure 'login' is the correct name for your login URL

    def test_login_page_loads_correctly(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')  # Make sure this is the correct template name
        self.assertIsInstance(response.context['form'], AuthenticationForm)

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': '12345'
        })
        self.assertRedirects(response, reverse('home'))  # Replace 'home' with your post-login redirect URL

    def test_login_failure(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')

    def test_login_redirect_for_authenticated_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('home'))  # Replace 'home' with your expected redirect URL for logged-in users