from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions (GET, HEAD, OPTIONS) are allowed to any request.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request.
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write permissions, ensure that the user is the owner.
        # Check if the object has 'user' and matches the request user.
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if the object has 'author' and matches the request user.
        if hasattr(obj, 'author') and obj.author == request.user:
            return True

        # Check if the object has 'profile' and matches the request user's profile.
        if hasattr(obj, 'profile') and obj.profile == request.user.profile:
            return True

        # Default to denying permission if ownership cannot be determined.
        return False
