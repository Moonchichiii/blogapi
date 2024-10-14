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
    AccountDeletionView,
    CustomTokenRefreshView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "activate/<str:uidb64>/<str:token>/",
        ActivateAccountView.as_view(),
        name="activate",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("current-user/", CurrentUserView.as_view(), name="current_user"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path(
        "password-reset/",
        include(
            [
                path("", auth_views.PasswordResetView.as_view(), name="password_reset"),
                path(
                    "done/",
                    auth_views.PasswordResetDoneView.as_view(),
                    name="password_reset_done",
                ),
                path(
                    "<uidb64>/<token>/",
                    auth_views.PasswordResetConfirmView.as_view(),
                    name="password_reset_confirm",
                ),
                path(
                    "complete/",
                    auth_views.PasswordResetCompleteView.as_view(),
                    name="password_reset_complete",
                ),
            ]
        ),
    ),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend_verification",
    ),
    path("setup-2fa/", SetupTwoFactorView.as_view(), name="setup_2fa"),
    path("update-email/", UpdateEmailView.as_view(), name="update_email"),
    path("delete-account/", AccountDeletionView.as_view(), name="delete_account"),
]
