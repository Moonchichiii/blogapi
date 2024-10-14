from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "value", "created_at"]
    list_filter = ["value", "created_at"]
    search_fields = ["user__profile_name", "post__title"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user", "post"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "post")
