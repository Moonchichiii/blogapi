from django.contrib import admin
from django.utils.html import format_html
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'birth_date', 'follower_count', 'following_count', 'popularity_score', 'profile_image']
    list_filter = ['location', 'birth_date']
    search_fields = ['user__profile_name', 'user__email', 'bio', 'location']
    readonly_fields = ['follower_count', 'following_count', 'popularity_score']
    fieldsets = [
        ('User Information', {'fields': ['user', 'bio', 'location', 'birth_date']}),
        ('Profile Image', {'fields': ['image']}),
        ('Statistics', {'fields': ['follower_count', 'following_count', 'popularity_score'], 'classes': ['collapse']}),
    ]

    def profile_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    profile_image.short_description = 'Profile Image'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')