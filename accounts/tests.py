from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from accounts.models import CustomUser
from accounts.tokens import account_activation_token
from profiles.models import Profile
from django.core import mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.activate_url = reverse("activate", kwargs={"uidb64": "test", "token": "test"})
        self.current_user_url = reverse("current_user")
        self.resend_verification_url = reverse("resend_verification")
        self.setup_2fa_url = reverse("setup_2fa")
        self.update_email_url = reverse("update_email")
        self.delete_account_url = reverse("delete_account")

    def tearDown(self):
        CustomUser.objects.all().delete()

    def create_user(self, email="testuser@example.com", profile_name="testuser", password="StrongPassword123!", is_active=False):
        user = CustomUser.objects.create_user(email=email, password=password, profile_name=profile_name)
        user.is_active = is_active
        user.save()
        return user

    def test_user_registration(self):
        """Test user registration with profile creation."""
        data = {
            "profile_name": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email="testuser@example.com").exists())
        self.assertTrue(Profile.objects.filter(user__email="testuser@example.com").exists())

    def test_user_login(self):
        """Test user login."""
        user = self.create_user(is_active=True)
        data = {"email": "testuser@example.com", "password": "StrongPassword123!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_logout(self):
        """Test user logout."""
        user = self.create_user(is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.create_user(is_active=False)
        data = {"email": "testuser@example.com", "password": "StrongPassword123!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["message"], "Account is not activated.")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        self.create_user(is_active=True)
        data = {"email": "testuser@example.com", "password": "WrongPassword123!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["message"], "Invalid email or password.")

    def test_account_activation(self):
        """Test account activation."""
        user = self.create_user(is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        url = reverse("activate", kwargs={"uidb64": uid, "token": token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @patch("accounts.views.send_mail")
    def test_send_activation_email(self, mock_send_mail):
        """Test sending activation email."""
        data = {
            "profile_name": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_mail.assert_called_once()
        self.assertIn("Activate your account", mock_send_mail.call_args[0][0])
        self.assertIn("newuser@example.com", mock_send_mail.call_args[0][3])

    def test_current_user_view(self):
        """Test retrieving current user details."""
        user = self.create_user(is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], user.email)
        self.assertEqual(response.data["profile"]["profile_name"], user.profile_name)

    def test_resend_verification_email(self):
        """Test resending verification email."""
        user = self.create_user(is_active=False)
        data = {"email": user.email}
        response = self.client.post(self.resend_verification_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Activate your account")

    @patch("accounts.views.TOTPDevice.objects.create")
    def test_setup_two_factor(self, mock_create_totp):
        """Test setting up two-factor authentication."""
        user = self.create_user(is_active=True)
        self.client.force_authenticate(user=user)
        mock_create_totp.return_value.config_url = "http://example.com/totp"
        mock_create_totp.return_value.key = "test_key"
        response = self.client.post(self.setup_2fa_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("config_url", response.data)
        self.assertIn("secret_key", response.data)

    def test_update_email(self):
        """Test updating user email."""
        user = self.create_user(is_active=True)
        self.client.force_authenticate(user=user)
        new_email = "newemail@example.com"
        data = {"email": new_email}
        response = self.client.patch(self.update_email_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, new_email)

    def test_delete_account(self):
        """Test deleting user account."""
        user = self.create_user(is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.delete_account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomUser.objects.filter(email=user.email).exists())

class CustomUserModelTestCase(TestCase):
    """Test cases for CustomUser model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = CustomUser.objects.create_user(email="user@example.com", profile_name="user", password="StrongPassword123!")
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.profile_name, "user")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_active)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = CustomUser.objects.create_superuser(email="admin@example.com", profile_name="admin", password="StrongPassword123!")
        self.assertEqual(admin_user.email, "admin@example.com")
        self.assertEqual(admin_user.profile_name, "admin")
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)

    def test_create_user_without_email(self):
        """Test creating a user without an email raises an error."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email="", profile_name="user", password="StrongPassword123!")

    def test_create_user_without_profile_name(self):
        """Test creating a user without a profile name raises an error."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email="user@example.com", profile_name="", password="StrongPassword123!")

class AccountsViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.activate_url = reverse("activate", kwargs={"uidb64": "test", "token": "test"})
        self.current_user_url = reverse("current_user")
        self.resend_verification_url = reverse("resend_verification")
        self.setup_2fa_url = reverse("setup_2fa")
        self.update_email_url = reverse("update_email")
        self.delete_account_url = reverse("delete_account")
        self.token_refresh_url = reverse("token_refresh")

    def create_user(self, email="testuser@example.com", profile_name="testuser", password="StrongPassword123!", is_active=True):
        user = User.objects.create_user(email=email, password=password, profile_name=profile_name)
        user.is_active = is_active
        user.save()
        return user

    def test_register_view_success(self):
        data = {
            "email": "newuser@example.com",
            "profile_name": "newuser",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Activate your account")

    def test_register_view_password_mismatch(self):
        data = {
            "email": "newuser@example.com",
            "profile_name": "newuser",
            "password": "StrongPassword123!",
            "password2": "DifferentPassword123!"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_view_existing_email(self):
        self.create_user()
        data = {
            "email": "testuser@example.com",
            "profile_name": "newuser",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_activate_account_view_success(self):
        user = self.create_user(is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        url = reverse("activate", kwargs={"uidb64": uid, "token": token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_account_view_invalid_token(self):
        user = self.create_user(is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = "invalid_token"
        url = reverse("activate", kwargs={"uidb64": uid, "token": token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_resend_verification_email_view_success(self):
        user = self.create_user(is_active=False)
        data = {"email": user.email}
        response = self.client.post(self.resend_verification_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Activate your account")

    def test_resend_verification_email_view_already_active(self):
        user = self.create_user(is_active=True)
        data = {"email": user.email}
        response = self.client.post(self.resend_verification_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_view_success(self):
        user = self.create_user()
        data = {"email": user.email, "password": "StrongPassword123!"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_view_invalid_credentials(self):
        user = self.create_user()
        data = {"email": user.email, "password": "WrongPassword123!"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_view_inactive_user(self):
        user = self.create_user(is_active=False)
        data = {"email": user.email, "password": "StrongPassword123!"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('accounts.views.TOTPDevice.objects.create')
    def test_setup_two_factor_view(self, mock_create_totp):
        user = self.create_user()
        self.client.force_authenticate(user=user)
        mock_device = MagicMock()
        mock_device.config_url = "otpauth://totp/testapp:testuser@example.com?secret=BASE32ENCODEDSTRING&issuer=testapp"
        mock_device.key = "BASE32ENCODEDSTRING"
        mock_create_totp.return_value = mock_device
        response = self.client.post(self.setup_2fa_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("config_url", response.data)
        self.assertIn("secret_key", response.data)

    def test_update_email_view_success(self):
        user = self.create_user()
        self.client.force_authenticate(user=user)
        new_email = "newemail@example.com"
        data = {"email": new_email}
        response = self.client.patch(self.update_email_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, new_email)

    def test_update_email_view_invalid_email(self):
        user = self.create_user()
        self.client.force_authenticate(user=user)
        data = {"email": "invalid_email"}
        response = self.client.patch(self.update_email_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_account_view(self):
        user = self.create_user()
        self.client.force_authenticate(user=user)
        response = self.client.post(self.delete_account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(email=user.email).exists())

    def test_logout_view(self):
        user = self.create_user()
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.cookies['refresh_token'].value, '')
        self.assertEqual(response.cookies['access_token'].value, '')

    def test_current_user_view(self):
        user = self.create_user()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)
        self.assertEqual(response.data['profile']['profile_name'], user.profile_name)

    def test_token_refresh_view(self):
        user = self.create_user()
        refresh = RefreshToken.for_user(user)
        data = {'refresh': str(refresh)}
        response = self.client.post(self.token_refresh_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue('access_token' in response.cookies)
        self.assertTrue('refresh_token' in response.cookies)

    def test_token_refresh_view_invalid_token(self):
        data = {'refresh': 'invalid_token'}
        response = self.client.post(self.token_refresh_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
