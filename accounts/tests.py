from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from accounts.models import CustomUser
from accounts.tokens import account_activation_token

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.activate_url = reverse('activate', kwargs={'uidb64': 'test', 'token': 'test'})
        self.current_user_url = reverse('current_user')
        print("Setup complete.")

    def tearDown(self):
        CustomUser.objects.all().delete()
        print("Teardown complete. Database cleaned.")

    def create_user(self, email='testuser@example.com', profile_name='testuser', password='StrongPassword123!', is_active=False):
        user = CustomUser.objects.create_user(email=email, profile_name=profile_name, password=password)
        user.is_active = is_active
        user.save()
        print(f"User created: {user.email}, Active: {user.is_active}")
        return user

    def test_user_registration(self):
        """Test user registration."""
        data = {"profile_name": "testuser", "email": "testuser@example.com", "password": "StrongPassword123!", "password2": "StrongPassword123!"}
        response = self.client.post(self.register_url, data, format='json')
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.get().email, 'testuser@example.com')
        self.assertFalse(CustomUser.objects.get().is_active)

    def test_user_login(self):
        """Test user login."""
        user = self.create_user(is_active=True)
        data = {"email": "testuser@example.com", "password": "StrongPassword123!"}
        response = self.client.post(self.login_url, data, format='json')
        print(f"Login response status: {response.status_code}")
        print(f"Login response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.create_user(is_active=False)
        data = {"email": "testuser@example.com", "password": "StrongPassword123!"}
        response = self.client.post(self.login_url, data, format='json')
        print(f"Login inactive user response status: {response.status_code}")
        print(f"Login inactive user response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], "Account is not activated.")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        self.create_user(is_active=True)
        data = {"email": "testuser@example.com", "password": "WrongPassword123!"}
        response = self.client.post(self.login_url, data, format='json')
        print(f"Login invalid credentials response status: {response.status_code}")
        print(f"Login invalid credentials response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], "Invalid credentials.")

    def test_account_activation(self):
        """Test account activation."""
        user = self.create_user(is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        url = reverse('activate', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        print(f"Account activation response status: {response.status_code}")
        print(f"Account activation response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @patch('accounts.views.send_mail')
    def test_send_activation_email(self, mock_send_mail):
        """Test sending activation email."""
        data = {"profile_name": "newuser", "email": "newuser@example.com", "password": "StrongPassword123!", "password2": "StrongPassword123!"}
        response = self.client.post(self.register_url, data, format='json')
        print(f"Send activation email response status: {response.status_code}")
        print(f"Send activation email response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_mail.assert_called_once()
        self.assertIn('Activate your account', mock_send_mail.call_args[0][0])
        self.assertIn('newuser@example.com', mock_send_mail.call_args[0][3])
        
        
    def test_current_user_view(self):
        """Test retrieving current user details."""
        user = self.create_user(is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(self.current_user_url)
        print(f"Current user view response status: {response.status_code}")
        print(f"Current user view response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)
        self.assertEqual(response.data['profile_name'], user.profile_name)
        
class CustomUserModelTestCase(TestCase):
    """Test cases for CustomUser model."""

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = CustomUser.objects.create_superuser(email='admin@example.com', profile_name='admin', password='StrongPassword123!')
        print(f"Superuser created: {admin_user.email}")
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertEqual(admin_user.profile_name, 'admin')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)
