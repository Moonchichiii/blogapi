from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

class Rating(models.Model):
    """Model representing a rating for a blog post."""
    
    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    post: models.ForeignKey = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, related_name="ratings"
    )
    value: models.IntegerField = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the Rating model."""
        unique_together = ("user", "post")
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', 'post']),
            models.Index(fields=['value']),
        ]

    def __str__(self) -> str:
        """Return a string representation of the rating."""
        return _("{user} rated {post} {value} stars").format(
            user=self.user.profile_name, post=self.post.title, value=self.value
        )
