from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _


class Rating(models.Model):
    """Store ratings for posts."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, related_name="ratings"
    )
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "post")
        indexes = [models.Index(fields=["post", "value"])]

    def __str__(self):
        """Return a string representation of the rating."""
        return _("{user} rated {post} {value} stars").format(
            user=self.user.profile_name, post=self.post.title, value=self.value
        )
