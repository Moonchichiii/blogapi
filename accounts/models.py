from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager



# Create your models here.



class CustomUserManager(BaseUserManager):
    def create_user(self, email, profile_name, password=None, **extra_fields):
        """Create and return a regular user with an email and profile_name."""
        if not email:
            raise ValueError('The Email field must be set')
        if not profile_name:
            raise ValueError('The Profile Name field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, profile_name=profile_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, profile_name, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, profile_name, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_name = models.CharField(max_length=255, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['profile_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.profile_name