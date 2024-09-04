from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from auth.models import CustomUser
from profiles.models import Profile
from allauth.account.models import EmailAddress

class AuthenticationTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('auth_register')
        cls.login_url = reverse('token_obtain_pair')
        cls.current_user_url = reverse('current_user')
        cls.update_email_url = reverse('update_email')

    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """Test if a user can register successfully."""
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
        """Test if a profile is created automatically when a user registers."""
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
        """Test if a user can log in with email and receive JWT tokens."""
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

    def test_email_uniqueness(self):
        """Test if the email must be unique."""
        CustomUser.objects.create_user(
            profile_name="uniqueuser1", email="uniqueuser1@example.com", password="StrongPassword123!"
        )

        data = {
            "profile_name": "newuser",
            "email": "uniqueuser1@example.com",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_profile_name_uniqueness(self):
        """Test if the profile_name must be unique."""
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
