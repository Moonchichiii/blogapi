from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.test import override_settings
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from accounts.models import CustomUser
from accounts.serializers import UserSerializer
from accounts.tokens import account_activation_token
from profiles.models import Profile


class AuthenticationTests(APITestCase):
    """Test suite for authentication-related functionalities."""

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('register')
        cls.login_url = reverse('login')
        cls.token_refresh_url = reverse('token_refresh')
        cls.current_user_url = reverse('current_user')
        cls.update_email_url = reverse('update_email')
        cls.delete_account_url = reverse('delete_account')

    def setUp(self):
        self.client = APIClient()
        OutstandingToken.objects.all().delete()
        BlacklistedToken.objects.all().delete()

    def tearDown(self):
        CustomUser.objects.all().delete()

    def generate_unique_email(self, prefix="test"):
        """Generate a unique email for testing."""
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    def test_user_registration(self):
        """Test user registration."""
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
        """Test profile creation on user registration."""
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
        """Test email uniqueness."""
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
        """Test profile name uniqueness."""
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
        self.assertIn('custom user with this profile name already exists',
                      response.data['profile_name'][0].lower())

    def test_password_mismatch(self):
        """Test password mismatch."""
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
        """Test invalid password."""
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
        """Test user login with email."""
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
        """Test login with unverified email."""
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
        """Test login with invalid credentials."""
        data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], "Invalid credentials")

    def test_token_refresh(self):
        """Test token refresh."""
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
        """Test account deletion."""
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
        """Test activation link expiry."""
        user = CustomUser.objects.create_user(
            profile_name="expiringuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!",
            is_active=False
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.get(reverse('activate', kwargs={'uidb64': uid, 'token': 'invalidtoken'}))
        self.assertEqual(response.status_code, 302)

    def test_2fa_setup(self):
        """Test 2FA setup."""
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
        """Test resend verification email."""
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

    @override_settings(REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
        'DEFAULT_THROTTLE_RATES': {'auth': '5/minute'}
    })
    def test_cannot_resend_verification_if_already_verified(self):
        """Test cannot resend verification if already verified."""
        user = CustomUser.objects.create_user(
            profile_name="alreadyverified",
            email="verifieduser@example.com",
            password="StrongPassword123!",
            is_active=True
        )
        data = {"email": user.email}
        response = self.client.post(reverse('resend_verification'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User already verified", response.data['error'])

    def test_activation_with_tampered_token(self):
        """Test activation with tampered token."""
        user = CustomUser.objects.create_user(
            profile_name="tampereduser",
            email=self.generate_unique_email(),
            password="StrongPassword123!",
            is_active=False
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        tampered_token = account_activation_token.make_token(user)[:-1]
        response = self.client.get(reverse('activate', kwargs={'uidb64': uid, 'token': tampered_token}))
        self.assertEqual(response.status_code, 302)

    def test_cannot_update_email_to_existing_one(self):
        """Test cannot update email to existing one."""
        user1 = CustomUser.objects.create_user(
            profile_name="user1",
            email="user1@example.com",
            password="StrongPassword123!"
        )
        user2 = CustomUser.objects.create_user(
            profile_name="user2",
            email="user2@example.com",
            password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user2)
        data = {"email": "user1@example.com"}
        response = self.client.patch(reverse('update_email'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A user with that email already exists", response.data['email'][0])

    def test_logout_invalidates_tokens(self):
        """Test logout invalidates tokens."""
        user = CustomUser.objects.create_user(
            profile_name="logoutuser",
            email="logoutuser@example.com",
            password="StrongPassword123!"
        )
        login_data = {
            'email': 'logoutuser@example.com',
            'password': 'StrongPassword123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        logout_response = self.client.post(reverse('logout'), {'refresh_token': login_response.data['refresh']})
        if logout_response.status_code != status.HTTP_200_OK:
            print("Logout response data:", logout_response.data)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

    def test_to_representation_different_user(self):
        """Test to_representation when the requesting user is different from the instance."""
        user1 = CustomUser.objects.create_user(
            profile_name="user1",
            email="user1@example.com",
            password="StrongPassword123!"
        )
        user2 = CustomUser.objects.create_user(
            profile_name="user2",
            email="user2@example.com",
            password="StrongPassword123!"
        )
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user2
        serializer = UserSerializer(user1, context={'request': request})
        data = serializer.data
        self.assertNotIn('email', data)
        self.assertNotIn('password', data)
        self.assertNotIn('password2', data)

    def test_validate_email_unique(self):
        """Test that validate_email accepts a unique email."""
        data = {'email': 'unique@example.com'}
        serializer = UserSerializer()
        validated_email = serializer.validate_email(data['email'])
        self.assertEqual(validated_email, data['email'])

    def test_validate_email_non_unique(self):
        """Test that validate_email raises error on duplicate email."""
        CustomUser.objects.create_user(
            profile_name="existinguser",
            email="existing@example.com",
            password="StrongPassword123!"
        )
        serializer = UserSerializer()
        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate_email('existing@example.com')
        self.assertIn('A user with that email already exists.', str(context.exception))
        
        
    def test_create_superuser(self):
        superuser = CustomUser.objects.create_superuser(
            email='admin@example.com',
            profile_name='admin',
            password='AdminPass123!'
            )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        
        
    def test_custom_user_str(self):
        user = CustomUser.objects.create_user(email='test@example.com', profile_name='testuser')
        self.assertEqual(str(user), 'test@example.com')
        
    