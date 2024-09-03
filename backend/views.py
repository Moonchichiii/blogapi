from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from dj_rest_auth.registration.views import RegisterView
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from profiles.serializers import UserSerializer

CustomUser = get_user_model()

# Custom Register View
class CustomRegisterView(RegisterView):
    def perform_create(self, serializer):
        user = serializer.save(self.request)
        send_email_confirmation(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "detail": "Verification email sent. Please confirm your email address to complete registration."
        }
        return Response(response.data, status=status.HTTP_201_CREATED)

# Custom Token Obtain Pair View
@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            print("Request Data:", request.data)
            user = CustomUser.objects.get(email=request.data.get('email'))
            email_address = EmailAddress.objects.get(user=user)
            if not email_address.verified:
                return Response({"detail": "Email is not verified."}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except EmailAddress.DoesNotExist:
            return Response({"detail": "Email address not found."}, status=status.HTTP_404_NOT_FOUND)

        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            secure_cookie = request.is_secure()
            response.set_cookie(
                'access_token',
                tokens['access'],
                httponly=True,
                secure=secure_cookie,
                samesite='None'
            )
            response.set_cookie(
                'refresh_token',
                tokens['refresh'],
                httponly=True,
                secure=secure_cookie,
                samesite='None'
            )
        return response


# Custom Token Refresh View
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            tokens = response.data
            secure_cookie = request.is_secure()
            response.set_cookie(
                'access_token',
                tokens['access'],
                httponly=True,
                secure=secure_cookie,
                samesite='None'
            )
        return response

# Update Email View
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



# Logout View
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

# Current User View
class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
