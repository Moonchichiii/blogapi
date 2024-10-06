from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions

from .managers import CustomUserManager
from .messages import STANDARD_MESSAGES


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model where email is the unique identifier for authentication.
    """
    email = models.EmailField(_('email address'), unique=True)
    profile_name = models.CharField(max_length=255, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['profile_name']

    objects = CustomUserManager()

    def __str__(self):
        return str(self.email)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email'),
            models.UniqueConstraint(fields=['profile_name'], name='unique_profile_name'),
        ]


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that checks for blacklisted tokens.
    """
    def authenticate(self, request):
        try:
            authentication_result = super().authenticate(request)
            if authentication_result is not None:
                user, validated_token = authentication_result
                jti = validated_token.get('jti')
                if BlacklistedAccessToken.objects.filter(jti=jti).exists():
                    raise exceptions.AuthenticationFailed(
                        STANDARD_MESSAGES['INVALID_TOKEN']['message'],
                        code='token_blacklisted'
                    )
                return user, validated_token
        except (InvalidToken, TokenError) as exc:
            raise exceptions.AuthenticationFailed(
                STANDARD_MESSAGES['INVALID_TOKEN']['message'],
            ) from exc
        return None


class BlacklistedAccessToken(models.Model):
    """
    Model to store blacklisted access tokens.
    """
    jti = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.jti
