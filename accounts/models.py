from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as the username field."""
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def profile_name(self):
        """Convenience property to access profile_name"""
        return self.profile.profile_name if hasattr(self, 'profile') else None
    
    @property
    def roles(self):
        """Get user roles for frontend use"""
        return {
            'is_admin': self.is_staff or self.is_superuser,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'is_verified': self.is_active
        }

    def has_role(self, role):
        """Check if user has a specific role"""
        return self.roles.get(f'is_{role}', False)

    def get_permissions(self):
        """Get user permissions based on roles"""
        permissions = set()
        
        if self.is_superuser:
            permissions.update(['manage_users', 'approve_posts', 'delete_posts'])
        if self.is_staff:
            permissions.update(['approve_posts', 'manage_content'])
        if self.is_active:
            permissions.add('create_posts')
            
        return list(permissions)

    def has_permission_to(self, request, permission):
        """Check if the user has a specific permission."""
        # Superusers automatically have all permissions
        if self.is_superuser:
            return True
        
        # Check if the user has the specified permission
        # by verifying against the permissions returned from `get_permissions`
        return permission in self.get_permissions()
