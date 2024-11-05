from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """Admin panel configuration for CustomUser."""

    model = CustomUser
    list_display = ("email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email",)  # Changed from string to tuple
    ordering = ("email",)
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make profile_name readonly in admin."""
        return super().get_readonly_fields(request, obj) + ('profile_name',)

    def get_inline_instances(self, request, obj=None):
        """Show profile information inline."""
        from profiles.admin import ProfileInline
        
        inlines = super().get_inline_instances(request, obj)
        if obj:  # Only show inline if object exists
            inlines.append(ProfileInline(self.model, self.admin_site))
        return inlines

admin.site.register(CustomUser, CustomUserAdmin)