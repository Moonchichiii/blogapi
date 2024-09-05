from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from accounts.models import CustomUser
from profiles.models import Profile
from allauth.account.models import EmailAddress
from django.utils.crypto import get_random_string
from unittest.mock import patch
from allauth.account.utils import send_email_confirmation

class AuthenticationTests(APITestCase):
    """
    Test cases for user authentication.
    """

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('auth_register')
        cls.login_url = reverse('token_obtain_pair')
        cls.token_refresh_url = reverse('token_refresh')
        cls.password_reset_url = reverse('password_reset')
        cls.current_user_url = reverse('current_user')
        cls.update_email_url = reverse('update_email')

    def setUp(self):
        self.client = APIClient()

    def generate_unique_email(self, prefix="test"):
        """
        Generate a unique email address.
        """
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    def test_user_registration(self):
        """
        Test if a user can register successfully.
        """
        data = {
            "profile_name": "testuser",
            "email": self.generate_unique_email(),
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email=data['email']).exists())

    def test_profile_creation_on_user_registration(self):
        """
        Test if a profile is automatically created on user registration.
        """
        data = {
            "profile_name": "testuser2",
            "email": self.generate_unique_email(),
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email=data['email'])
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_email_uniqueness(self):
        """
        Test that duplicate email registration is blocked.
        """
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
        self.assertEqual(response.data['email'][0], 'This email is already registered.')

    def test_profile_name_uniqueness(self):
        """
        Test that duplicate profile names are blocked.
        """
        CustomUser.objects.create_user(
            profile_name="uniqueuser", email="uniqueuser@example.com", password="StrongPassword123!"
        )

        data = {
            "profile_name": "uniqueuser",
            "email": self.generate_unique_email(),
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile_name', response.data)
        self.assertEqual(response.data['profile_name'][0], 'This profile name is already taken.')

    def test_password_mismatch(self):
        """
        Test password mismatch during registration.
        """
        data = {
            "profile_name": "testuser4",
            "email": self.generate_unique_email(),
            "password1": "StrongPassword123!",
            "password2": "DifferentPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], "The two password fields didn't match.")

    def test_invalid_password(self):
        """
        Test invalid (too weak) password during registration.
        """
        data = {
            "profile_name": "testuser5",
            "email": self.generate_unique_email(),
            "password1": "weak",
            "password2": "weak"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password1', response.data)
        self.assertTrue("This password is too short" in response.data['password1'][0])

    def test_user_login_with_email(self):
        """
        Test if a user can login successfully with email.
        """
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

    def test_login_with_unverified_email(self):
        """
        Test that login fails for unverified email addresses.
        """
        user = CustomUser.objects.create_user(
            profile_name="unverifieduser", email=self.generate_unique_email(), password="StrongPassword123!"
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)

        data = {
            "email": user.email,
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "Please verify your email before logging in.")

    def test_login_with_invalid_credentials(self):
        """
        Test login with incorrect credentials.
        """
        data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], "No active account found")

    def test_token_refresh(self):
        """
        Test if the token refresh works correctly.
        """
        user = CustomUser.objects.create_user(
            profile_name="testuserrefresh", email="testrefresh@example.com", password="StrongPassword123!"
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        # Login to get refresh token
        login_data = {"email": "testrefresh@example.com", "password": "StrongPassword123!"}
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Test token refresh
        refresh_response = self.client.post(self.token_refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_password_reset_request(self):
        """
        Test if password reset request works correctly.
        """
        user = CustomUser.objects.create_user(
            profile_name="resetuser", email="resetuser@example.com", password="StrongPassword123!"
        )
        data = {"email": user.email}
        response = self.client.post(self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_account_deletion(self):
        """
        Test if a user can delete their account.
        """
        user = CustomUser.objects.create_user(
            profile_name="deletetestuser", email="deletetestuser@example.com", password="StrongPassword123!"
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        # Login the user
        login_data = {"email": "deletetestuser@example.com", "password": "StrongPassword123!"}
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')

        # Request account deletion
        response = self.client.post(reverse('account_delete'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomUser.objects.filter(email="deletetestuser@example.com").exists())
