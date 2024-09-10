from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['truncated_content', 'author', 'post', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'author']
    search_fields = ['content', 'author__profile_name', 'post__title']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['author', 'post']
    fieldsets = [
        ('Comment Information', {'fields': ['author', 'post', 'content']}),
        ('Approval', {'fields': ['is_approved']}),
        ('Metadata', {'fields': ['created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    def truncated_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Content'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'post')