from django.conf import settings
from django.db import models
from posts.models import Post

class Comment(models.Model):
    """
    Represents a comment on a blog post.
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
    content = models.TextField(help_text="Content of the comment.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Time when the comment was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Time when the comment was last updated.")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]

    def __str__(self):
        """
        Returns a string representation of the Comment.
        """
        return f'Comment by {self.author.profile_name} on {self.post.title}'
