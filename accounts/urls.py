from django.urls import path
from .views import (
    RegisterView, 
    ActivateAccountView, 
    LoginView, 
    CustomTokenRefreshView, 
    UpdateEmailView, 
    LogoutView, 
    AccountDeletionView, 
    CurrentUserView,
    ResendVerificationEmailView,
    SetupTwoFactorView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),    
    path('setup-2fa/', SetupTwoFactorView.as_view(), name='setup_2fa'),
    path('update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('delete-account/', AccountDeletionView.as_view(), name='delete_account'),
    path('current-user/', CurrentUserView.as_view(), name='current_user'),
]
