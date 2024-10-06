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
from .messages import STANDARD_MESSAGES

User = get_user_model()


class AuthRateThrottle(AnonRateThrottle):
    """Throttle class for authentication."""
    scope = 'auth'


class RegisterView(APIView):
    """Register a new user and send activation email."""
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        """Handle POST request for user registration."""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            self.send_activation_email(user, request)
            return Response(STANDARD_MESSAGES['REGISTRATION_SUCCESS'], status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def send_activation_email(user, request):
        """Send account activation email to the user."""
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{request.scheme}://{request.get_host()}/api/accounts/activate/{uid}/{token}/"
        send_mail(
            'Activate your account',
            f'Click this link to activate your account: {activation_link}',
            'noreply@theblog.com',
            [user.email],
            fail_silently=False,
        )


class ActivateAccountView(APIView):
    """Activate user account using the provided token."""
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Handle GET request for account activation."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            redirect_url = (
                f"{settings.FRONTEND_URL}/activate/{uidb64}/{token}?"
                f"status=success&access_token={str(refresh.access_token)}&refresh_token={str(refresh)}"
            )
            return redirect(redirect_url)

        return redirect(f"{settings.FRONTEND_URL}/activate/{uidb64}/{token}?status=error")


class ResendVerificationEmailView(APIView):
    """Resend verification email to the user."""

    def post(self, request):
        """Handle POST request to resend verification email."""
        email = request.data.get('email')
        if not email:
            return Response(STANDARD_MESSAGES['USER_NOT_FOUND'], status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(STANDARD_MESSAGES['USER_NOT_FOUND'], status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({'error': 'User already verified'}, status=status.HTTP_400_BAD_REQUEST)

        RegisterView.send_activation_email(user, request)
        return Response({'message': 'Verification email resent successfully'}, status=status.HTTP_200_OK)


class SetupTwoFactorView(APIView):
    """Setup two-factor authentication for the user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle POST request to setup 2FA."""
        user = request.user
        device = TOTPDevice.objects.filter(user=user, name="default").first()
        if device:
            return Response({'error': 'A 2FA device already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        device = TOTPDevice.objects.create(user=user, name="default")
        return Response({'config_url': device.config_url, 'secret_key': device.key}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """Login user and return JWT tokens."""
    throttle_classes = [AuthRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST request for user login."""
        user = User.objects.filter(email=request.data.get('email')).first()
        if user and user.check_password(request.data.get('password')):
            if not user.is_active:
                return Response(STANDARD_MESSAGES['ACCOUNT_NOT_ACTIVATED'], status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            return Response({'refresh': str(refresh), 'access': str(access_token)}, status=status.HTTP_200_OK)
        return Response(STANDARD_MESSAGES['INVALID_CREDENTIALS'], status=status.HTTP_401_UNAUTHORIZED)


class CustomTokenRefreshView(TokenRefreshView):
    """Refresh JWT tokens and set them in cookies."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle POST request to refresh JWT tokens."""
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            response.set_cookie(
                'access_token', tokens['access'], httponly=True, secure=request.is_secure(), samesite='Lax'
            )
        return response


class UpdateEmailView(generics.UpdateAPIView):
    """Update the email address of the authenticated user."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        """Get the authenticated user."""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """Handle PUT request to update email."""
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(STANDARD_MESSAGES['EMAIL_UPDATE_SUCCESS'], status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout the authenticated user by blacklisting the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle POST request to logout user."""
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({"detail": "Invalid refresh token.", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(STANDARD_MESSAGES['LOGOUT_SUCCESS'], status=status.HTTP_200_OK)


class AccountDeletionView(APIView):
    """Delete the authenticated user's account."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle POST request to delete account."""
        request.user.delete()
        return Response(STANDARD_MESSAGES['ACCOUNT_DELETION_SUCCESS'], status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveAPIView):
    """Retrieve the authenticated user's details."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        """Get the authenticated user."""
        return self.request.user

    def get_serializer_context(self):
        """Add request context to serializer."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
