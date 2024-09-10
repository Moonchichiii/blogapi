from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .serializers import UserSerializer
from .tokens import account_activation_token
from django.shortcuts import redirect
from django.conf import settings


User = get_user_model()

class CustomAnonRateThrottle(AnonRateThrottle):
    rate = '5/minute'

class RegisterView(APIView):
    throttle_classes = [CustomAnonRateThrottle]
   
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.save()
            self.send_activation_email(user, request)
            return Response({
                "message": "User registered successfully. Please check your email to activate your account.",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def send_activation_email(self, user, request):
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{request.scheme}://{request.get_host()}/api/accounts/activate/{uid}/{token}/"
        send_mail(
            'Activate your account',
            f'Click this link to activate your account: {activation_link}',
            'noreply@yourdomain.com',
            [user.email],
            fail_silently=False,
        )
class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Redirect to frontend with tokens and success status
            redirect_url = (f"{settings.FRONTEND_URL}/activate/{uidb64}/{token}?"
                            f"status=success&"
                            f"access_token={str(refresh.access_token)}&"
                            f"refresh_token={str(refresh)}")
            return redirect(redirect_url)
        else:
            # Redirect to frontend with an error parameter
            return redirect(f"{settings.FRONTEND_URL}/activate/{uidb64}/{token}?status=error")



class ResendVerificationEmailView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email, is_active=False).first()
        if not user:
            return Response({'error': 'User not found or already verified'}, status=status.HTTP_404_NOT_FOUND)

        # Generate verification token
        token = account_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{request.scheme}://{request.get_host()}/api/accounts/activate/{uid}/{token}/"

        # Send verification email
        send_mail(
            'Activate your account',
            f'Click this link to activate your account: {activation_link}',
            'noreply@yourdomain.com',
            [user.email],
            fail_silently=False,
        )

        return Response({'message': 'Verification email resent successfully'}, status=status.HTTP_200_OK)
    
class SetupTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        device, created = TOTPDevice.objects.get_or_create(user=user, name="default")
        
        if created:
            device.save()

        config_url = device.config_url

        return Response({
            'config_url': config_url,
            'secret_key': device.key,
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    throttle_classes = [CustomAnonRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        user = User.objects.filter(email=request.data.get('email')).first()
        if user and user.check_password(request.data.get('password')):
            if not user.is_active:
                return Response({"message": "Please activate your account."}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            response.set_cookie('access_token', tokens['access'], httponly=True, secure=request.is_secure(), samesite='Lax')
        return response

class UpdateEmailView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.delete()
        return Response({"detail": "Account deleted successfully."}, status=status.HTTP_200_OK)

class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context