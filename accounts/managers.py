from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser model."""

    def create_user(self, email, profile_name, password=None, **extra_fields):
        """Create and return a regular user with an email and profile name."""
        if not email:
            raise ValueError("The Email field must be set")
        if not profile_name:
            raise ValueError("The Profile Name field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, profile_name=profile_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, profile_name, password=None, **extra_fields):
        """Create and return a superuser with an email and profile name."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, profile_name, password, **extra_fields)
