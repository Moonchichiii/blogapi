from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractUser, BaseUserManager

# ------------------------------
# Custom User Manager
# ------------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, profile name, and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        if not profile_name:
            raise ValueError('The Profile Name field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, profile_name=profile_name, **extra_fields)
        user.set_password(password)
        try:
            user.save(using=self._db)
        except IntegrityError:
            raise IntegrityError("A user with this email or profile name already exists.")
        return user

    def create_superuser(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, profile name, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, profile_name, password, **extra_fields)


# ------------------------------
# Custom User Model
# ------------------------------
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_name = models.CharField(max_length=255, unique=True)
    username = None  

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['profile_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.profile_name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email'),
            models.UniqueConstraint(fields=['profile_name'], name='unique_profile_name'),
        ]
