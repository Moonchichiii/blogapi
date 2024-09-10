from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions are allowed to any request.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'profile'):
            return obj.profile == request.user.profile
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False