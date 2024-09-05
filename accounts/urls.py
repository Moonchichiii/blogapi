from django.urls import path, include
from dj_rest_auth.registration.views import ResendEmailVerificationView , VerifyEmailView
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    UpdateEmailView,
    LogoutView,
    CurrentUserView,
    AccountDeletionView,
    CustomVerifyEmailView,
)

urlpatterns = [
    # Authentication and User Management
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('user/', CurrentUserView.as_view(), name='current_user'),
    path('update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('delete-account/', AccountDeletionView.as_view(), name='account_delete'),
    # Password Reset
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # Dj-rest-auth and Allauth Views
    path('', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('account-confirm-email/<str:uidb64>/<str:token>/', CustomVerifyEmailView.as_view(), name='account_confirm_email'),

    path('account-resend-verification/', ResendEmailVerificationView.as_view(), name="account_resend_verification"),
]
