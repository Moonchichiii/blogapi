from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_approved', 'created_at', 'average_rating', 'comment_count']
    list_filter = ['is_approved', 'created_at', 'author']
    search_fields = ['title', 'content', 'author__username', 'author__email']
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'total_ratings']
    fieldsets = [
        ('Post Information', {'fields': ['title', 'author', 'content', 'image']}),
        ('Approval', {'fields': ['is_approved']}),
        ('Statistics', {'fields': ['created_at', 'updated_at', 'average_rating', 'total_ratings'], 'classes': ['collapse']}),
    ]
    
    def average_rating(self, obj):
        avg = obj.average_rating
        return format_html('<span style="color: green;">{:.2f}</span>', avg) if avg else 'No ratings'
    average_rating.short_description = 'Avg Rating'

    def comment_count(self, obj):
        count = obj.comments.count()
        url = reverse('admin:comments_comment_changelist') + f'?post__id__exact={obj.id}'
        return format_html('<a href="{}">{} comments</a>', url, count)
    comment_count.short_description = 'Comments'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            avg_rating=Avg('ratings__value'),
            comments_count=Count('comments')
        )