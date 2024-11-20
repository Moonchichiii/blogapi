from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow only owners of an object or admin users to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # If obj is the user object
        if isinstance(obj, User):
            return obj == request.user or request.user.is_staff or request.user.is_superuser

        # If obj has a 'user' or 'author' attribute
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff or request.user.is_superuser
        elif hasattr(obj, 'author'):
            return obj.author == request.user or request.user.is_staff or request.user.is_superuser

        # Default to deny permission
        return False


class IsAdminOrSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow admin staff or superusers.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )
