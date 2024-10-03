from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow owners, staff, or superusers to edit an object.
    Read permissions are allowed to any request.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are allowed if the user is the owner, staff, or superuser.
        if hasattr(obj, 'author') and obj.author == request.user:
            return True

        if hasattr(obj, 'user') and obj.user == request.user:
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        return False
