from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from accounts.models import CustomUser
from profiles.models import Profile
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from accounts.tokens import account_activation_token

class AuthenticationTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Define URLs for various endpoints
        cls.register_url = reverse('register')
        cls.login_url = reverse('login')
        cls.token_refresh_url = reverse('token_refresh')
        cls.current_user_url = reverse('current_user')
        cls.update_email_url = reverse('update_email')
        cls.delete_account_url = reverse('delete_account')

    def setUp(self):
        # Initialize the API client for each test
        self.client = APIClient()

    def tearDown(self):
        # Clean up the database after each test
        CustomUser.objects.all().delete()

    def generate_unique_email(self, prefix="test"):
        # Generate a unique email address for testing
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    def test_user_registration(self):
        # Test user registration
        data = {
            "profile_name": "testuser",
            "email": self.generate_unique_email(),
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email=data['email']).exists())

    def test_profile_creation_on_user_registration(self):
        # Test profile creation upon user registration
        data = {
            "profile_name": "testuser2",
            "email": self.generate_unique_email(),
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email=data['email'])
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_email_uniqueness(self):
        # Test that email addresses must be unique
        data = {
            'email': 'testuser@example.com',
            'profile_name': 'testuser',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }
        self.client.post(self.register_url, data, format='json')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('A user with that email already exists.', response.data['email'][0])

    def test_profile_name_uniqueness(self):
        # Test that profile names must be unique
        CustomUser.objects.create_user(
            profile_name="uniqueuser",
            email="uniqueuser@example.com",
            password="StrongPassword123!"
        )
        data = {
            "profile_name": "uniqueuser",
            "email": self.generate_unique_email(),
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile_name', response.data)
        self.assertIn('custom user with this profile name already exists', response.data['profile_name'][0].lower())

    def test_password_mismatch(self):
        # Test that passwords must match
        data = {
            "profile_name": "testuser4",
            "email": self.generate_unique_email(),
            "password": "StrongPassword123!",
            "password2": "DifferentPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertIn("Password fields didn't match.", response.data['password'])

    def test_invalid_password(self):
        # Test that passwords must meet complexity requirements
        data = {
            "profile_name": "testuser5",
            "email": self.generate_unique_email(),
            "password": "weak",
            "password2": "weak"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertIn("This password must contain at least 8 characters.", response.data['password'][0])

    def test_user_login_with_email(self):
        # Test user login with email and password
        user = CustomUser.objects.create_user(
            profile_name="testuser3",
            email="testuser3@example.com",
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        data = {
            "email": "testuser3@example.com",
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_unverified_email(self):
        # Test login with an unverified email
        user = CustomUser.objects.create_user(
            profile_name="unverifieduser",
            email=self.generate_unique_email(),
            password="StrongPassword123!"
        )
        user.is_active = False
        user.save()
        data = {
            "email": user.email,
            "password": "StrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], "Please activate your account.")

    def test_login_with_invalid_credentials(self):
        # Test login with invalid credentials
        data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], "Invalid credentials")

    def test_token_refresh(self):
        # Test token refresh functionality
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
        )
        user.is_active = True
        user.save()
        login_data = {
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', login_response.data)
        self.assertIn('access', login_response.data)

    def test_account_deletion(self):
        # Test account deletion
        user = CustomUser.objects.create_user(
            profile_name="deletetestuser",
            email="deletetestuser@example.com",
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        login_data = {"email": "deletetestuser@example.com", "password": "StrongPassword123!"}
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        response = self.client.post(self.delete_account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomUser.objects.filter(email="deletetestuser@example.com").exists())

    def test_activation_link_expiry(self):
        # Test activation link expiry
        user = CustomUser.objects.create_user(
            profile_name="expiringuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!",
            is_active=False
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        
        # Modify the token or simulate an expired token
        response = self.client.get(reverse('activate', kwargs={'uidb64': uid, 'token': 'invalidtoken'}))
        self.assertEqual(response.status_code, 302)  # Assuming it redirects to an error page

    def test_2fa_setup(self):
        # Test 2FA setup
        user = CustomUser.objects.create_user(
            profile_name="2fauser",
            email="2fauser@example.com",
            password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('setup_2fa'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('config_url', response.data)
        self.assertIn('secret_key', response.data)

    def test_resend_verification_email(self):
        # Test resending verification email
        user = CustomUser.objects.create_user(
            profile_name="resenduser",
            email="resenduser@example.com",
            password="StrongPassword123!",
            is_active=False
        )
        data = {"email": user.email}
        response = self.client.post(reverse('resend_verification'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Verification email resent successfully", response.data['message'])

    def test_rate_limiting_on_registration(self):
        # Test rate limiting on registration
        for _ in range(6):  # Assuming rate limit is 5 per minute
            self.client.post(self.register_url, {
                "profile_name": f"ratelimituser{_}",
                "email": self.generate_unique_email(),
                "password": "StrongPassword123!",
                "password2": "StrongPassword123!"
            }, format='json')

        # Check if the sixth request is rate-limited
        response = self.client.post(self.register_url, {
            "profile_name": "ratelimituser6",
            "email": self.generate_unique_email(),
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
