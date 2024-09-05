from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from dj_rest_auth.registration.views import RegisterView
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site

from .tokens import account_activation_token
from profiles.serializers import UserSerializer
from .serializers import CustomRegisterSerializer

CustomUser = get_user_model()

# ------------------------------
# Helper Function to Send Activation Email
# ------------------------------
def activateEmail(request, user, to_email):
    mail_subject = 'Activate your user account.'
    message = render_to_string('accounts/email_template.html', {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()

# ------------------------------
# Custom Register View
# ------------------------------
class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        send_email_confirmation(self.request, user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": "Verification email sent. Please confirm your email address to complete registration."},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

# ------------------------------
# Custom Token Obtain Pair View
# ------------------------------
@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = CustomUser.objects.get(email=request.data['email'])
            email_address = EmailAddress.objects.get(user=user, email=user.email)
            if not email_address.verified:
                return Response({"detail": "Please verify your email before logging in."}, status=status.HTTP_403_FORBIDDEN)

            # Set tokens in cookies
            response.set_cookie('access_token', response.data['access'], httponly=True, secure=request.is_secure(), samesite='Lax')
            response.set_cookie('refresh_token', response.data['refresh'], httponly=True, secure=request.is_secure(), samesite='Lax')
        return response

# ------------------------------
# Custom Email Verification View
# ------------------------------
class CustomVerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user and account_activation_token.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save()
                return Response({"detail": "Email confirmed successfully!"}, status=status.HTTP_200_OK)
            return Response({"detail": "Account already activated."}, status=status.HTTP_200_OK)
        
        return Response({"detail": "Activation link is invalid!"}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------
# Custom Token Refresh View
# ------------------------------
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            secure_cookie = request.is_secure()
            response.set_cookie('access_token', tokens['access'], httponly=True, secure=secure_cookie, samesite='None')
        return response

# ------------------------------
# Update Email View
# ------------------------------
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

# ------------------------------
# Logout View
# ------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

# ------------------------------
# Account Deletion View
# ------------------------------
class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.delete()
        return Response({"detail": "Account deleted successfully."}, status=status.HTTP_200_OK)

# ------------------------------
# Current User View
# ------------------------------
class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
