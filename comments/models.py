from django.db import models
from django.conf import settings
from posts.models import Post
from django.contrib.contenttypes.fields import GenericRelation
from tags.models import ProfileTag

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)
    tags = GenericRelation(ProfileTag)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.profile_name} on {self.post.title}'