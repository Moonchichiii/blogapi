from rest_framework import permissions

class BasePermission(permissions.BasePermission):
    """Base class for all custom permissions with enhanced role checking."""
    
    def has_admin_permission(self, request):
        """Check if user has admin-level access."""
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.has_role('admin') or request.user.has_role('staff')
    
    def has_permission_to(self, request, permission):
        """Check if user has a specific permission."""
        if not (request.user and request.user.is_authenticated):
            return False
        return permission in request.user.get_permissions()
    
    def is_owner(self, obj, user):
        """Check if user is the owner of an object."""
        if not user or not user.is_authenticated:
            return False
        if hasattr(obj, 'author'):
            return obj.author == user
        if hasattr(obj, 'user'):
            return obj.user == user
        return False

class IsOwnerOrReadOnly(BasePermission):
    """Allow read access to all, but only owners can edit."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            self.is_owner(obj, request.user) or 
            self.has_admin_permission(request)
        )

class IsPostOwnerOrStaff(BasePermission):
    """Enhanced post permissions with specific permission checks."""
    
    def has_permission(self, request, view):
        """Check general permission to interact with posts."""
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Creating posts requires 'create_posts' permission
        if request.method == 'POST':
            return self.has_permission_to(request, 'create_posts')
            
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Anyone can view approved posts
        if request.method in permissions.SAFE_METHODS:
            if getattr(obj, 'is_approved', True):
                return True
                
            # Only owners and staff can view unapproved posts
            return (
                self.is_owner(obj, request.user) or 
                self.has_admin_permission(request)
            )
        
        # Check specific permissions for different actions
        if request.method in ['PUT', 'PATCH']:
            if self.is_owner(obj, request.user):
                return True
            return self.has_permission_to(request, 'manage_content')
            
        if request.method == 'DELETE':
            if self.is_owner(obj, request.user):
                return True
            return self.has_permission_to(request, 'delete_posts')
        
        return False

class IsProfileOwnerOrAdmin(BasePermission):
    """Enhanced profile permissions."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Profile owners can always edit their own profiles
        if self.is_owner(obj, request.user):
            return True
            
        # Admins can manage any profile if they have the permission
        return self.has_permission_to(request, 'manage_users')

class IsAdminUser(BasePermission):
    """Permission for admin-only actions."""
    
    def has_permission(self, request, view):
        return self.has_admin_permission(request)

class CanApprovePost(BasePermission):
    """Specific permission for post approval actions."""
    
    def has_permission(self, request, view):
        return self.has_permission_to(request, 'approve_posts')

    def has_object_permission(self, request, view, obj):
        return self.has_permission_to(request, 'approve_posts')
