from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["truncated_content", "author_link", "post_link", "created_at"]
    list_filter = ["created_at", "author"]
    search_fields = ["content", "author__profile_name", "post__title"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["author", "post"]
    fieldsets = [
        ("Comment Information", {"fields": ["author", "post", "content"]}),
        (
            "Metadata",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),  # Moved is_approved from here
    ]

    def truncated_content(self, obj):
        """
        Truncate the content displayed in the admin list view for better readability.
        """
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    truncated_content.short_description = "Content"

    def author_link(self, obj):
        """
        Display a link to the author's profile for quick navigation in the admin.
        """
        url = reverse("admin:accounts_customuser_change", args=[obj.author.pk])
        return format_html('<a href="{}">{}</a>', url, obj.author.profile_name)

    author_link.short_description = "Author"

    def post_link(self, obj):
        """
        Display a link to the related post for easy access in the admin.
        """
        url = reverse("admin:posts_post_change", args=[obj.post.pk])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)

    post_link.short_description = "Post"

    def get_queryset(self, request):
        """
        Optimize queryset to include related author and post objects for performance.
        """
        return super().get_queryset(request).select_related("author", "post")
