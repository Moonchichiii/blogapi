from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from .messages import STANDARD_MESSAGES


class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser model, handling user and superuser creation.
    """

    def create_user(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, profile name, and password.
        """
        if not email:
            raise ValueError(STANDARD_MESSAGES['USER_NOT_FOUND']['message'])
        if not profile_name:
            raise ValueError(_("The Profile Name field must be set"))

        email = self.normalize_email(email)
        user = self.model(email=email, profile_name=profile_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, profile name, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, profile_name, password, **extra_fields)
