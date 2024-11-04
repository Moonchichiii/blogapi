from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import (
    RegisterView,
    ActivateAccountView,
    LoginView,
    LogoutView,
    CurrentUserView,
    ResendVerificationEmailView,
    UpdateEmailView,
    SetupTwoFactorView,
    TwoFactorVerifyView,
    AccountDeletionView,
    CustomTokenRefreshView,
    UpdateProfileNameView
    
)

urlpatterns = [
    # User registration and activation
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    
        
    # User login and logout
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    
    # Current user info
    path("current-user/", CurrentUserView.as_view(), name="current_user"),
    
     path("update-profile-name/", UpdateProfileNameView.as_view(), name="update_profile_name"),
    # Token refresh
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    
    # Password reset
    path(
        "password-reset/",
        include([
            path("", auth_views.PasswordResetView.as_view(), name="password_reset"),
            path("done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
            path("<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
            path("complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
        ]),
    ),
    
    # Resend verification email
    path("resend-verification/", ResendVerificationEmailView.as_view(), name="resend_verification"),
    
    # Two-factor authentication setup and verification
    path("setup-2fa/", SetupTwoFactorView.as_view(), name="setup_2fa"),
    path("verify-2fa/", TwoFactorVerifyView.as_view(), name="verify_2fa"), 
    
    # Update email
    path("update-email/", UpdateEmailView.as_view(), name="update_email"),
    
    # Account deletion
    path("delete-account/", AccountDeletionView.as_view(), name="delete_account"),
]
