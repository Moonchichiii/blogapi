from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, profile_name, password=None, **extra_fields):
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
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, profile_name, password, **extra_fields)