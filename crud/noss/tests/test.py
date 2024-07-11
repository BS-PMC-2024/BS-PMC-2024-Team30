# myapp/tests.py
from django.test import TestCase
from django.urls import reverse
from noss.models import MyModel

class MyModelTestCase(TestCase):
    def setUp(self):
        MyModel.objects.create(name="Test Name", description="Test Description")

    def test_model_creation(self):
        """Test if the MyModel object is created correctly."""
        obj = MyModel.objects.get(name="Test Name")
        self.assertEqual(obj.name, "Test Name")
        self.assertEqual(obj.description, "Test Description")

# class MyViewTestCase(TestCase):
#     def test_view_status_code(self):
#         """Test if the view returns a 200 status code."""
#         response = self.client.get(reverse('myview'))
#         self.assertEqual(response.status_code, 200)

#     def test_view_template(self):
#         """Test if the view uses the correct template."""
#         response = self.client.get(reverse('myview'))
#         self.assertTemplateUsed(response, 'myapp/myview.html')
