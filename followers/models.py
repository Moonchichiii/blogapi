from django.conf import settings
from django.db import models

class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='following',
        on_delete=models.CASCADE
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='followers',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['followed']),
            models.Index(fields=['created_at']),  # Added indexing for `created_at`
        ]

    def __str__(self):
        return f"{self.follower.profile_name} follows {self.followed.profile_name}"
