from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import UserRegistrationSerializer, LoginSerializer, UserSerializer
from .tokens import account_activation_token
from .messages import STANDARD_MESSAGES
# from .models import CustomUser

User = get_user_model()



class RegisterView(generics.CreateAPIView):
    """User registration"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        self.send_activation_email(user)
    
    def send_activation_email(self, user):
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
        subject = 'Activate your account'
        message = f'Hi {user.profile_name},\n\nPlease click the link below to activate your account:\n{activation_link}\n\nThank you!'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

class ActivateAccountView(APIView):
    """Account activation"""
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

            response = Response({
                "message": "Your email has been successfully verified.",
                "type": "success",
                "user": UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)

            # Set tokens in cookies
            response.set_cookie('access_token', access_token, httponly=True, secure=request.is_secure())
            response.set_cookie('refresh_token', refresh_token, httponly=True, secure=request.is_secure())

            return response

        return Response({
            "message": "Invalid or expired activation link.",
            "type": "error"
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """Resend verification email"""
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
        RegisterView().send_activation_email(user)
        return Response({
            "message": "Verification email resent successfully.",
            "type": "success"
        }, status=status.HTTP_200_OK)

class SetupTwoFactorView(APIView):
    """Set up 2FA"""
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
            "message": STANDARD_MESSAGES['SUCCESS']['2FA_SETUP'],
            "type": "success",
            "config_url": device.config_url,
            "secret_key": device.key
        }, status=status.HTTP_200_OK)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful.",
                "type": "success",
                "user": UserSerializer(user, context={'request': request}).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)
        else:
            errors = serializer.errors
            if 'non_field_errors' in errors:
                error_message = errors['non_field_errors'][0]
                if error_message == "Account is not activated.":
                    return Response({
                        "message": error_message,
                        "type": "error"
                    }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        "message": "Invalid credentials.",
                        "type": "error"
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    "message": "Invalid input.",
                    "type": "error",
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenRefreshView(TokenRefreshView):
    """Token refresh and set cookie"""
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            response.set_cookie('access_token', tokens['access'], httponly=True, secure=request.is_secure())
            response.set_cookie('refresh_token', tokens['refresh'], httponly=True, secure=request.is_secure())
        return response

class UpdateEmailView(generics.UpdateAPIView):
    """Update email"""
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
                "type": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "Failed to update email.",
            "type": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """User logout"""
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response({
                "message": "Logout successful.",
                "type": "success"
            }, status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        except Exception as e:
            return Response({
                "message": "Invalid refresh token.",
                "type": "error",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AccountDeletionView(APIView):
    """Delete account"""
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        user.delete()
        return Response({
            "message": "Your account has been successfully deleted.",
            "type": "success"
        }, status=status.HTTP_200_OK)

class CurrentUserView(generics.RetrieveAPIView):
    """Retrieve current user details"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user
