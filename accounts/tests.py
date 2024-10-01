from unittest.mock import patch
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.test import override_settings
from rest_framework import serializers, status, exceptions
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import CustomUser, BlacklistedAccessToken, CustomJWTAuthentication
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

# serialization tests 

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
        self.assertIn('This profile name is already taken.', response.data['profile_name'][0])
        
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
        self.assertIn('this profile name is already taken.', response.data['profile_name'][0].lower())


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
        
    def test_2fa_setup_when_device_already_exists(self):
        """Test that 2FA setup fails when the device already exists."""
        user = CustomUser.objects.create_user(
            profile_name="2fauser", email="2fauser@example.com", password="StrongPassword123!")
        self.client.force_authenticate(user=user)    
        
        TOTPDevice.objects.create(user=user, name="default")
        response = self.client.post(reverse('setup_2fa'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A 2FA device already exists', response.data.get('error', ''))

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
        
        
class UserSerializerUpdateTests(TestCase):
    """Tests for updating users via UserSerializer."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='updateuser@example.com',
            profile_name='updateuser',
            password='StrongPassword123!'
        )
        self.serializer_context = {'request': None}

    def test_update_email_success(self):
        """Test updating the user's email to a new unique email."""
        data = {'email': 'newemail@example.com'}
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_update_profile_name_success(self):
        """Test updating the user's profile_name to a new unique profile_name."""
        data = {'profile_name': 'newprofile'}
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile_name, 'newprofile')

    def test_update_password_success(self):
        """Test updating the user's password."""
        data = {
            'password': 'NewStrongPassword123!',
            'password2': 'NewStrongPassword123!'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPassword123!'))

    def test_update_email_to_existing_one(self):
        """Test updating the user's email to an existing email raises an error."""
        CustomUser.objects.create_user(
            email='existingemail@example.com',
            profile_name='existinguser',
            password='StrongPassword123!'
        )
        data = {'email': 'existingemail@example.com'}
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], 'A user with that email already exists.')

    def test_update_profile_name_to_existing_one(self):
        CustomUser.objects.create_user(
            email='anotheremail@example.com',
            profile_name='existingprofile',
            password='StrongPassword123!'
            )
        data = {'profile_name': 'existingprofile'}
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('profile_name', serializer.errors)
        self.assertEqual(str(serializer.errors['profile_name'][0]), 'This profile name is already taken.')


    def test_update_password_mismatch(self):
        """Test that a password mismatch during update raises a validation error."""
        data = {
            'password': 'NewStrongPassword123!',
            'password2': 'DifferentPassword123!'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        self.assertEqual(serializer.errors['password'][0], "Password fields didn't match.")

    def test_update_with_no_changes(self):
        """Test updating with no changes does not alter the user."""
        data = {}
        serializer = UserSerializer(instance=self.user, data=data, partial=True, context=self.serializer_context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updateuser@example.com')
        self.assertEqual(self.user.profile_name, 'updateuser')
class CustomJWTAuthenticationTests(TestCase):
    """Tests for the CustomJWTAuthentication class."""
    def setUp(self):
        self.factory = RequestFactory()
        self.authenticator = CustomJWTAuthentication()
        self.user = CustomUser.objects.create_user(
            email='authuser@example.com',
            profile_name='authuser',
            password='StrongPassword123!'
            )
        self.user.is_active = True
        self.user.save()
        
    def generate_token(self):
        """Helper method to generate a valid JWT access token."""
        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)
    
    def test_authenticate_with_valid_token(self):
        """Test authentication with a valid JWT token."""
        token = self.generate_token()
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        user, validated_token = self.authenticator.authenticate(request)
        self.assertEqual(user, self.user)
        self.assertIsNotNone(validated_token)        

    def test_authenticate_with_blacklisted_token(self):
        """Test authentication fails with a blacklisted JWT token."""
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        jti = access_token['jti']
        BlacklistedAccessToken.objects.create(jti=jti)
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {str(access_token)}'
        
        with self.assertRaises(exceptions.AuthenticationFailed) as context:            
            self.authenticator.authenticate(request)
            self.assertEqual(str(context.exception), 'Access token has been blacklisted')

    def test_authenticate_with_invalid_token(self):
                """Test authentication with an invalid JWT token."""
                invalid_token = 'invalidtoken123'
                request = self.factory.get('/')
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {invalid_token}'
                with self.assertRaises(exceptions.AuthenticationFailed):
                    self.authenticator.authenticate(request)

class ResendVerificationEmailTests(APITestCase):
    def test_resend_verification_email_without_email(self):
        """Test that an error is returned if no email is provided."""
        response = self.client.post(reverse('resend_verification'), data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Email is required')
        
        
class RegisterViewInvalidEmailTests(APITestCase):
    def test_register_with_invalid_email_format(self):
        """Test registering a user with an invalid email format."""
        data = {
            "profile_name": "testuser",
            "email": "invalid-email",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], 'Enter a valid email address.')


class LoginViewTests(APITestCase):
    def test_login_with_missing_email(self):
        """Test that login fails if no email is provided."""
        data = {
            "password": "StrongPassword123!"
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], "Invalid credentials")

    def test_login_with_missing_password(self):
        """Test that login fails if no password is provided."""
        data = {
            "email": "testuser@example.com"
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], "Invalid credentials")


class UserSerializerCreateTests(TestCase):
    def test_create_user_with_existing_email(self):
        """Test that creating a user with an existing email returns the correct validation error."""
        CustomUser.objects.create_user(
            email='duplicate@example.com',
            profile_name='duplicateprofile',
            password='StrongPassword123!'
        )

        data = {
            'email': 'duplicate@example.com',
            'profile_name': 'newprofile',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }

        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], 'A user with that email already exists.')

            
class UserSerializerRepresentationTests(TestCase):
    def test_to_representation_excludes_sensitive_fields(self):
        """Test that sensitive fields are excluded when retrieving user data for another user."""
        user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            profile_name='user1',
            password='StrongPassword123!'
        )
        user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            profile_name='user2',
            password='StrongPassword123!'
        )
        
        request = APIRequestFactory().get('/')
        request.user = user2
        serializer = UserSerializer(user1, context={'request': request})
        
        data = serializer.data
        self.assertNotIn('email', data)
        self.assertNotIn('password', data)

class UpdateEmailViewTests(APITestCase):
    def test_unauthorized_update_email(self):
        """Test that an unauthorized user cannot update email."""
        data = {"email": "newemail@example.com"}
        response = self.client.patch(reverse('update_email'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Authentication credentials were not provided.')
        
class UserSerializerProfileNameTests(TestCase):
    def test_profile_name_with_special_characters(self):
        """Test that profile name with special characters raises a validation error."""
        data = {
            'email': 'user@example.com',
            'profile_name': 'invalid@name', 
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('profile_name', serializer.errors)
        self.assertEqual(serializer.errors['profile_name'][0], 'Profile name can only contain letters, numbers, and underscores.')



class RegisterViewLongEmailTests(APITestCase):
    def test_register_with_extremely_long_email(self):
        """Test registering a user with an extremely long email."""
        long_email = f"{'a'*250}@example.com"
        data = {
            "profile_name": "longemailuser",
            "email": long_email,
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!"
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('Ensure this field has no more than 254 characters.', response.data['email'][0])

        
        
class UpdateEmailMalformedEmailTests(APITestCase):
    def test_update_email_with_malformed_email(self):
        """Test updating the user's email to a malformed email."""
        user = CustomUser.objects.create_user(
            email="validemail@example.com",
            profile_name="validprofile",
            password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)
        data = {"email": "invalid-email-format"}
        response = self.client.patch(reverse('update_email'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('Enter a valid email address.', response.data['email'][0])
        
class LoginAfterAccountDeletionTests(APITestCase):
    def test_login_after_account_deletion(self):
        """Test that login fails after account deletion."""
        user = CustomUser.objects.create_user(
            profile_name="deleteusertest",
            email="deleteusertest@example.com",
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()

        # Delete the account
        self.client.force_authenticate(user=user)
        self.client.post(reverse('delete_account'))
        
        # Attempt to log in after deletion
        login_data = {"email": "deleteusertest@example.com", "password": "StrongPassword123!"}
        response = self.client.post(reverse('login'), login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], "Invalid credentials")
        

class ActivateAccountInvalidTokenTests(APITestCase):
    def test_activate_account_with_invalid_token(self):
        """Test account activation with an invalid token."""
        user = CustomUser.objects.create_user(
            profile_name="invalidtokenuser",
            email="invalidtokenuser@example.com",
            password="StrongPassword123!",
            is_active=False
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.get(reverse('activate', kwargs={'uidb64': uid, 'token': 'invalid-token'}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("status=error", response.url)
        
        
class UserSerializerEmptyProfileNameTests(TestCase):
    def test_empty_profile_name(self):
        """Test that an empty profile name raises a validation error."""
        data = {
            'email': 'user@example.com',
            'profile_name': '',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('profile_name', serializer.errors)
        self.assertEqual(serializer.errors['profile_name'][0], 'This field may not be blank.')


class UserSerializerShortPasswordTests(TestCase):
    def test_password_too_short(self):
        """Test that a password that is too short raises a validation error."""
        data = {
            'email': 'user@example.com',
            'profile_name': 'validprofile',
            'password': 'short',
            'password2': 'short'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        self.assertIn('This password must contain at least 8 characters.', serializer.errors['password'][0])
        
        
class UserSerializerPasswordMismatchTests(TestCase):
    def test_password_mismatch(self):
        """Test that non-matching passwords raise a validation error."""
        data = {
            'email': 'user@example.com',
            'profile_name': 'validprofile',
            'password': 'StrongPassword123!',
            'password2': 'DifferentPassword123!'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        self.assertEqual(serializer.errors['password'][0], "Password fields didn't match.")


class UserSerializerLongProfileNameTests(TestCase):
    def test_profile_name_too_long(self):
        """Test that an extremely long profile name raises a validation error."""
        long_profile_name = 'a' * 151  
        data = {
            'email': 'user@example.com',
            'profile_name': long_profile_name,
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('profile_name', serializer.errors)
        self.assertIn('Ensure this field has no more than 150 characters.', serializer.errors['profile_name'][0])






