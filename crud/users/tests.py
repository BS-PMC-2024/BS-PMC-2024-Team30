from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

class LoginAndRegisterTests(TestCase):
    
    def test_login_template_rendered(self):
        response = self.client.get(reverse('login'))  # Replace 'login' with your login view name
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        
        # Check context data if needed
        # context = response.context
        # self.assertIn('key', context)
        
        # Check if form is rendered
        self.assertIsInstance(response.context['form'], AuthenticationForm)
    
    def test_register_template_rendered(self):
        response = self.client.get(reverse('register'))  # Replace 'register' with your register view name
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        
        # Check context data if needed
        # context = response.context
        # self.assertIn('key', context)
        
        # Check if form is rendered
        self.assertIsInstance(response.context['form'], UserCreationForm)
    
    def test_login_form_submission(self):
        # Simulate form submission for login
        form_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(reverse('login'), form_data)  # Replace 'login' with your login view name
        self.assertEqual(response.status_code, 200)  # Adjust status code based on your implementation
        # Add assertions for successful login behavior or redirects
    
    def test_register_form_submission(self):
        # Simulate form submission for register
        form_data = {
            'username': 'newuser',
            'password1': 'newpassword',
            'password2': 'newpassword'
        }
        response = self.client.post(reverse('register'), form_data)  # Replace 'register' with your register view name
        self.assertEqual(response.status_code, 200)  # Adjust status code based on your implementation
        # Add assertions for successful registration behavior or redirects
