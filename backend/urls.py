from django.contrib import admin
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
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/auth/user/', CurrentUserView.as_view(), name='current_user'),    
    path('api/auth/update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    path('api/auth/account-resend-verification/', ResendEmailVerificationView.as_view(), name="account_resend_verification"),
]
