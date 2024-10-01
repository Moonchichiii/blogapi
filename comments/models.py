from django.db import models
from django.conf import settings
from posts.models import Post

class Comment(models.Model):
    """
    Model representing a comment on a blog post.
    """
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]

    def __str__(self):
        """
        String representation of the Comment model.
        """
        return f'Comment by {self.author.profile_name} on {self.post.title}'