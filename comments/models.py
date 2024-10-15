from django.conf import settings
from django.db import models
from posts.models import Post

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(help_text="Content of the comment.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["post", "-created_at"])]

    def __str__(self):
        return f"Comment by {self.author.profile_name} on {self.post.title}"