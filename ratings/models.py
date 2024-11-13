from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="ratings")
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "post")
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', 'post']),
            models.Index(fields=['value']),
        ]

    def __str__(self):
        return f"{self.user.profile.profile_name} rated {self.post.title} {self.value} stars"
