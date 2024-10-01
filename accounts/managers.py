from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser model, handling user and superuser creation.
    """

    def create_user(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, profile name, and password.

        Args:
            email (str): The email address of the user.
            profile_name (str): The profile name of the user.
            password (str, optional): The password for the user. Defaults to None.
            **extra_fields: Additional fields for the user model.

        Raises:
            ValueError: If the email or profile name is not provided.

        Returns:
            user: The created user instance.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not profile_name:
            raise ValueError(_('The Profile Name field must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, profile_name=profile_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, profile name, and password.

        Args:
            email (str): The email address of the superuser.
            profile_name (str): The profile name of the superuser.
            password (str, optional): The password for the superuser. Defaults to None.
            **extra_fields: Additional fields for the superuser model.

        Returns:
            user: The created superuser instance.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, profile_name, password, **extra_fields)
