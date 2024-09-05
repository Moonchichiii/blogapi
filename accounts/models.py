from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token

# ------------------------------
# Custom User Manager
# ------------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a regular user with the given email, profile name, and password.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not profile_name:
            raise ValueError(_('The Profile Name field must be set'))

        email = self.normalize_email(email)
        user = self.model(email=email, profile_name=profile_name, **extra_fields)
        user.set_password(password)
        try:
            user.save(using=self._db)
        except IntegrityError:
            raise IntegrityError(_("A user with this email or profile name already exists."))
        return user

    def create_superuser(self, email, profile_name, password=None, **extra_fields):
        """
        Create and save a superuser with the given email, profile name, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, profile_name, password, **extra_fields)

# ------------------------------
# Custom User Model
# ------------------------------
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_name = models.CharField(max_length=255, unique=True)
    username = None  # We don't use username for authentication.

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

    # ------------------------------
    # Model Methods for Common Logic
    # ------------------------------

    def activate_account(self):
        """
        Activate the user's account.
        """
        self.is_active = True
        self.save()

    def send_activation_email(self, request):
        """
        Send account activation email to the user.
        """
        mail_subject = 'Activate your account'
        message = render_to_string('accounts/email_template.html', {
            'user': self,
            'domain': get_current_site(request).domain,
            'uid': urlsafe_base64_encode(force_bytes(self.pk)),
            'token': account_activation_token.make_token(self),
            'protocol': 'https' if request.is_secure() else 'http'
        })
        email = EmailMessage(mail_subject, message, to=[self.email])
        email.send()

    def is_verified(self):
        """
        Check if the user's email has been verified.
        """
        return EmailAddress.objects.filter(user=self, verified=True).exists()

    def reset_password(self, request, new_password):
        """
        Reset the user's password and send a confirmation email.
        """
        self.set_password(new_password)
        self.save()
        

