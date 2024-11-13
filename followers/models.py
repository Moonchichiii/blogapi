from django.db import models
from django.conf import settings

class Follow(models.Model):
    """Model representing a follow relationship between users."""
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "followed")
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["followed"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.follower.profile.profile_name} follows {self.followed.profile.profile_name}"
