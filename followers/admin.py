from django.contrib import admin
from .models import Follow

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'followed', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__profile_name', 'followed__profile_name']
    readonly_fields = ['created_at']
    raw_id_fields = ['follower', 'followed']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('follower', 'followed')