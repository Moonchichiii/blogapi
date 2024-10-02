from unittest.mock import patch
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers, status, exceptions
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CustomUser, BlacklistedAccessToken, CustomJWTAuthentication
from accounts.serializers import UserSerializer
from accounts.tokens import account_activation_token
from profiles.models import Profile
from accounts.messages import STANDARD_MESSAGES


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
        self.factory = APIRequestFactory()
        OutstandingToken.objects.all().delete()
        BlacklistedToken.objects.all().delete()

    def generate_unique_email(self, prefix="test"):
        """Generate a unique email for testing."""
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    ### --- User Registration Tests --- ###

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

    def test_registration_with_invalid_data(self):
        """Test that registration fails with missing profile_name and invalid password."""
        data = {
            "profile_name": "",
            "email": "invalidemail@",
            "password": "weak",
            "password2": "weak"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile_name', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_custom_user_str_method(self):
        """Test the string representation of CustomUser."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
        )
        self.assertEqual(str(user), 'testuser@example.com')

    def test_custom_jwt_authentication(self):
        """Test CustomJWTAuthentication."""
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
        response = self.client.post(self.login_url, login_data, format='json')
        access_token = response.data['access']

    
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.get(self.current_user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Given token not valid for any token type')

    ### --- Validation Tests --- ###

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
        self.assertIn(str(STANDARD_MESSAGES['INVALID_CREDENTIALS']['message']), response.data['email'][0])

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
        self.assertIn(str(STANDARD_MESSAGES['INVALID_CREDENTIALS']['message']), response.data['profile_name'][0])

    def test_profile_name_uniqueness_case_insensitive(self):
        """Test profile name uniqueness (case-insensitive)."""
        CustomUser.objects.create_user(
            profile_name="UniqueUser",
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
        self.assertIn(str(STANDARD_MESSAGES['INVALID_CREDENTIALS']['message']), response.data['profile_name'][0])

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
        self.assertIn(str(STANDARD_MESSAGES['INVALID_CREDENTIALS']['message']), response.data['password'])

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
        self.assertIn(str(STANDARD_MESSAGES['PASSWORD_TOO_SHORT']['message']), response.data['password'][0])

    ### --- Login Tests --- ###

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
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['ACCOUNT_NOT_ACTIVATED']['message'])

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['INVALID_CREDENTIALS']['message'])

    ### --- Account Activation Tests --- ###

    @patch('accounts.views.send_mail')
    def test_send_activation_email(self, mock_send_mail):
        """Test activation email is sent during registration."""
        data = {
            "profile_name": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_mail.assert_called_once()
        # Validate email arguments
        self.assertIn('Activate your account', mock_send_mail.call_args[0][0])
        self.assertIn('newuser@example.com', mock_send_mail.call_args[0][3])

    def test_account_activation_with_invalid_token(self):
        """Test that activation with an invalid token fails."""
        user = CustomUser.objects.create_user(
            profile_name="inactiveuser", email="inactiveuser@example.com", password="StrongPassword123!", is_active=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token = 'invalid-token'
        response = self.client.get(reverse('activate', kwargs={'uidb64': uid, 'token': invalid_token}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('status=error', response.url)

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

    ### --- Token Management Tests --- ###

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

    ### --- Account Deletion Tests --- ###

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

    ### --- 2FA Tests --- ###

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

    def test_2fa_setup_when_device_already_exists(self):
        """Test that 2FA setup fails when the device already exists."""
        user = CustomUser.objects.create_user(
            profile_name="2fauser", email="2fauser@example.com", password="StrongPassword123!")
        self.client.force_authenticate(user=user)
        TOTPDevice.objects.create(user=user, name="default")
        response = self.client.post(reverse('setup_2fa'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A 2FA device already exists', response.data.get('error', ''))

    ### --- Email Verification Tests --- ###

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
        self.assertIn('Verification email resent successfully', response.data['message'])

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

    ### --- Blacklisted Token Tests --- ###

    def test_blacklisted_access_token_creation(self):
        """Test creating a BlacklistedAccessToken instance."""
        jti = 'unique_jti_token'
        token = BlacklistedAccessToken.objects.create(jti=jti)
        self.assertEqual(token.jti, jti)
        self.assertTrue(BlacklistedAccessToken.objects.filter(jti=jti).exists())

    def test_blacklisted_access_token_str(self):
        """Test the string representation of BlacklistedAccessToken."""
        jti = 'unique_jti_token_str'
        token = BlacklistedAccessToken.objects.create(jti=jti)
        self.assertEqual(str(token), jti)

    ### --- User Serializer Tests --- ###

    def test_user_serializer_create(self):
        """Test UserSerializer create method."""
        data = {
            'email': 'newuser@example.com',
            'profile_name': 'newuser',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.profile_name, 'newuser')

    def test_user_serializer_update(self):
        """Test UserSerializer update method."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
        )
        data = {
            'email': 'updated@example.com',
            'profile_name': 'updateduser'
        }
        serializer = UserSerializer(instance=user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.profile_name, 'updateduser')
        
    def test_resend_verification_email_invalid_email(self):
            """Test resend verification email with invalid email."""
            data = {"email": "nonexistent@example.com"}
            response = self.client.post(reverse('resend_verification'), data, format='json')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['USER_NOT_FOUND']['message'])

    def test_update_email(self):
            """Test updating user email."""
            user = CustomUser.objects.create_user(
                email='testuser@example.com',
                profile_name='testuser',
                password='StrongPassword123!'
            )
            self.client.force_authenticate(user=user)
            data = {"email": "newemail@example.com"}
            response = self.client.patch(self.update_email_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['EMAIL_UPDATE_SUCCESS']['message'])
            user.refresh_from_db()
            self.assertEqual(user.email, "newemail@example.com")
            
            
            
    def test_logout(self):
        """Test user logout."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
            )
        refresh = RefreshToken.for_user(user)
        self.client.force_authenticate(user=user)
        data = {"refresh_token": str(refresh)}
        response = self.client.post(reverse('logout'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['LOGOUT_SUCCESS']['message'])


    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
            )
        self.client.force_authenticate(user=user)
        data = {"refresh_token": "invalidtoken"}
        response = self.client.post(reverse('logout'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid refresh token.", response.data['detail'])
        
    def test_custom_user_creation_and_manager(self):
        """Test CustomUser creation and manager methods."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
            )
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.profile_name, 'testuser')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        
        superuser = CustomUser.objects.create_superuser(
                    email='admin@example.com',
                    profile_name='admin',
                    password='StrongPassword123!'
                )
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertEqual(superuser.profile_name, 'admin')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        
    def test_user_serializer_to_representation(self):
        """Test UserSerializer to_representation method."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
            )
        serializer = UserSerializer(instance=user)
        data = serializer.data
        self.assertNotIn('password', data)
        self.assertNotIn('password2', data)
        # Test representation for non-owner
        
        request = self.factory.get('/')
        request.user = CustomUser.objects.create_user(
            email='otheruser@example.com',
            profile_name='otheruser',
            password='StrongPassword123!'
            )
        serializer.context['request'] = request
        data = serializer.to_representation(user)
        self.assertNotIn('email', data)

    def test_activate_account_invalid_token(self):
        """Test account activation with invalid token."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!',
            is_active=False  
            )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)   
        response = self.client.get(reverse('activate', kwargs={'uidb64': uid, 'token': 'invalidtoken'}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('status=error', response.url)

    def test_custom_token_refresh(self):
        """Test CustomTokenRefreshView."""
        user = CustomUser.objects.create_user(
        email='testuser@example.com',
        profile_name='testuser',
        password='StrongPassword123!'
        )
        refresh = RefreshToken.for_user(user)
        data = {'refresh': str(refresh)}
        response = self.client.post(reverse('token_refresh'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('access_token', response.cookies)

    def test_logout_without_token(self):
        """Test logout without providing a refresh token."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
            )
        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST),
        self.assertIn("Refresh token is required.", response.data['detail'])
        
    def test_custom_jwt_authentication_with_blacklisted_token(self):
        """Test CustomJWTAuthentication with a blacklisted token."""
        user = CustomUser.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='StrongPassword123!'
            )
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        BlacklistedAccessToken.objects.create(jti=access_token['jti'])    
    
        auth = CustomJWTAuthentication()
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {str(access_token)}'
        
        with self.assertRaises(exceptions.AuthenticationFailed) as context:
            auth.authenticate(request)
        self.assertEqual(str(context.exception), STANDARD_MESSAGES['INVALID_TOKEN']['message'])
