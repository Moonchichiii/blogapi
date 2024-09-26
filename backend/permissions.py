from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions are allowed to any request.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request (GET, HEAD, OPTIONS).
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the object has 'user' and ensure it matches the request user.
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check for 'author' attribute.
        if hasattr(obj, 'author'):
            return obj.author == request.user
        
        # Check for 'profile' attribute.
        if hasattr(obj, 'profile'):
            return obj.profile == request.user.profile

        # Default to deny permission if object ownership cannot be determined.
        return False
