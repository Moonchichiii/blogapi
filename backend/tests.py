from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from profiles.models import CustomUser, Profile
from allauth.account.models import EmailAddress

class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth_register')
        self.login_url = reverse('token_obtain_pair')
        self.current_user_url = reverse('current_user')
        self.update_email_url = reverse('update_email')
        

    def test_user_registration(self):
        """Test if a user can register successfully with email and profile_name."""
        data = {
            "profile_name": "testuser",
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
            "profile_name": "testuser2",
            "email": "testuser2@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email="testuser2@example.com")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_user_login_with_email(self):
        """Test if a user can log in with email and receive tokens."""
        user = CustomUser.objects.create_user(
            profile_name="testuser3", email="testuser3@example.com", password="StrongPassword123!"
    )
    
    
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
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
        user = CustomUser.objects.create_user(
            profile_name="testuser4", email="testuser4@example.com", password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)
        data = {"email": "newemail@example.com"}
        response = self.client.patch(self.update_email_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, "newemail@example.com")

    def test_get_current_user(self):
        """Test if a logged-in user can fetch their current user data."""
        user = CustomUser.objects.create_user(
            profile_name="testuser5", email="testuser5@example.com", password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "testuser5@example.com")
        self.assertEqual(response.data['profile_name'], "testuser5")

    def test_profile_name_uniqueness(self):
        """Test if profile_name must be unique."""
        CustomUser.objects.create_user(
            profile_name="uniqueuser", email="uniqueuser@example.com", password="StrongPassword123!"
        )
        data = {
            "profile_name": "uniqueuser",
            "email": "uniqueuser2@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile_name', response.data)
        
    def test_email_uniqueness(self):
        """Test if email must be unique."""

        CustomUser.objects.create_user(
            profile_name="user1", email="user1@example.com", password="StrongPassword123!"
        )
        
        
        data = {
            "profile_name": "newuser",
            "email": "user1@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        
    def tearDown(self):
        CustomUser.objects.all().delete()
        Profile.objects.all().delete()

