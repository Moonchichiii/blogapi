from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView



from .serializers import UserSerializer
from .tokens import account_activation_token
from .messages import MESSAGES


User = get_user_model()

class AuthRateThrottle(AnonRateThrottle):
    """Throttle class for authentication."""
    scope = 'auth'

import logging

# Set up logging
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug("Received registration request with data: %s", request.data)
        print("Received registration request with data:", request.data)
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            logger.info("User created successfully: %s", user)
            print("User created successfully:", user)
            
            self.send_activation_email(user, request)
            return Response({
                "message": "Registration successful. Please check your email to activate your account.",
                "type": "success"
            }, status=status.HTTP_201_CREATED)
        
        logger.error("Registration failed with errors: %s", serializer.errors)
        print("Registration failed with errors:", serializer.errors)
        
        return Response({
            "message": "Registration failed. Please check your input.",
            "type": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def send_activation_email(user, request):
        logger.debug("Sending activation email to user: %s", user)
        print("Sending activation email to user:", user)
        
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{request.scheme}://{request.get_host()}/api/accounts/activate/{uid}/{token}/"
        
        logger.debug("Activation link: %s", activation_link)
        print("Activation link:", activation_link)
        
        send_mail(
            'Activate your account',
            MESSAGES['EMAIL_VERIFICATION_LINK'].format(verification_link=activation_link),
            'noreply@theblog.com',
            [user.email],
            fail_silently=False,
        )
        
        logger.info("Activation email sent to: %s", user.email)
        print("Activation email sent to:", user.email)


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            user_data = UserSerializer(user, context={'request': request}).data

            return Response({
                "message": "Email verified successfully.",
                "type": "success",
                "tokens": {
                    "access": access_token,
                    "refresh": refresh_token
                },
                "user": user_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Invalid activation link.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                "message": "Email is required.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({
                "message": "User not found.",
                "type": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({
                "message": "User already verified.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

        RegisterView.send_activation_email(user, request)
        return Response({
            "message": "Verification email resent successfully.",
            "type": "success"
        }, status=status.HTTP_200_OK)


class SetupTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        device = TOTPDevice.objects.filter(user=user, name="default").first()
        if device:
            return Response({
                "message": "Two-factor authentication is already set up.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        device = TOTPDevice.objects.create(user=user, name="default")
        return Response({
            "message": "Two-factor authentication set up successfully.",
            "type": "success",
            "config_url": device.config_url,
            "secret_key": device.key
        }, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Get email and password from the request data
        email = request.data.get('email')
        password = request.data.get('password')

        # Check if the email and password are provided
        if not email or not password:
            return Response({
                "message": "Email and password are required.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the user by email
        user = User.objects.filter(email=email).first()

        # Check if user exists and password matches
        if user and user.check_password(password):
            if not user.is_active:
                return Response({
                    "message": "Account not activated. Please check your email.",
                    "type": "error"
                }, status=status.HTTP_403_FORBIDDEN)

            # Generate JWT tokens for the user
            refresh = RefreshToken.for_user(user)

            # Use the UserSerializer to return user data
            user_data = UserSerializer(user, context={'request': request}).data

            return Response({
                "message": "Login successful.",
                "type": "success",
                "tokens": {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                },
                "user": user_data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Invalid credentials.",
            "type": "error"
        }, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            response.set_cookie(
                'access_token', tokens['access'], httponly=True, secure=request.is_secure(), samesite='Lax'
            )
        return response

class UpdateEmailView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "message": "Your email has been successfully updated.",
                "type": "success"
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "Failed to update email.",
            "type": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({"detail": "Invalid refresh token.", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Logout successful.",
            "type": "success"
        }, status=status.HTTP_205_RESET_CONTENT)

class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.delete()
        return Response({
            "message": "Your account has been successfully deleted.",
            "type": "success"
        }, status=status.HTTP_200_OK)

class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context