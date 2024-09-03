from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions are allowed to any request, so we'll always allow GET, HEAD, or OPTIONS requests.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object
        if hasattr(obj, 'author'):
            return obj.author == request.user.profile
        elif hasattr(obj, 'profile'):
            return obj.profile == request.user.profile
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False
