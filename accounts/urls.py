from django.urls import path
from .views import (
    RegisterView, 
    ActivateAccountView, 
    LoginView, 
    CustomTokenRefreshView, 
    UpdateEmailView, 
    LogoutView, 
    AccountDeletionView, 
    CurrentUserView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('update-email/', UpdateEmailView.as_view(), name='update_email'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('delete-account/', AccountDeletionView.as_view(), name='delete_account'),
    path('current-user/', CurrentUserView.as_view(), name='current_user'),
]