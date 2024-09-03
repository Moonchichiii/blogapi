from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from profiles.models import CustomUser, Profile

class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth_register')
        self.login_url = reverse('token_obtain_pair')
        self.current_user_url = reverse('current_user')
        self.update_email_url = reverse('update_email')

    def test_user_registration(self):
        """Test if a user can register successfully."""
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email="testuser@example.com").exists())

    def test_profile_creation_on_user_registration(self):
        """Test if a profile is created when a new user registers."""
        data = {
            "username": "testuser2",
            "email": "testuser2@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email="testuser2@example.com")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_user_login(self):
        """Test if a user can log in and receive tokens."""
        CustomUser.objects.create_user(username="testuser3", email="testuser3@example.com", password="StrongPassword123!")
        data = {
            "email": "testuser3@example.com",
            "password": "StrongPassword123!"
    }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_update_email(self):
        """Test if a logged-in user can update their email."""
        user = CustomUser.objects.create_user(username="testuser4", email="testuser4@example.com", password="StrongPassword123!")
        self.client.force_authenticate(user=user)
        data = {"email": "newemail@example.com"}
        response = self.client.patch(self.update_email_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, "newemail@example.com")

    def test_get_current_user(self):
        """Test if a logged-in user can fetch their current user data."""
        user = CustomUser.objects.create_user(username="testuser5", email="testuser5@example.com", password="StrongPassword123!")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "testuser5@example.com")
