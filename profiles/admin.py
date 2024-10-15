from django.contrib import admin
from django.utils.html import format_html
from .models import Profile
from popularity.models import PopularityMetrics

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "get_popularity_score", "profile_image", "follower_count", "following_count"]
    list_filter = ["user__is_active"]
    search_fields = ["user__profile_name", "user__email", "bio"]
    readonly_fields = ["get_popularity_score", "follower_count", "following_count"]
    fieldsets = [
        ("User Information", {"fields": ["user", "bio"]}),
        ("Profile Image", {"fields": ["image"]}),
        ("Statistics", {"fields": ["get_popularity_score", "follower_count", "following_count"], "classes": ["collapse"]}),
    ]

    def profile_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"

    profile_image.short_description = "Profile Image"

    def get_popularity_score(self, obj):
        try:
            return obj.user.popularity_metrics.popularity_score
        except PopularityMetrics.DoesNotExist:
            return 0.0

    get_popularity_score.short_description = "Popularity Score"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")