from django.urls import path, include
from dj_rest_auth.registration.views import VerifyEmailView, ResendEmailVerificationView
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    UpdateEmailView,
    LogoutView,
    CurrentUserView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('user/', CurrentUserView.as_view(), name='current_user'),
    path('update-email/', UpdateEmailView.as_view(), name='update_email'),
    
    # Dj-rest-auth and Allauth views
    path('', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    path('account-resend-verification/', ResendEmailVerificationView.as_view(), name="account_resend_verification"),
]
