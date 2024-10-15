from django.db import models
from django.conf import settings

class PopularityMetrics(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='popularity_metrics')
    follower_count = models.PositiveIntegerField(default=0)
    average_post_rating = models.FloatField(default=0.0)
    post_count = models.PositiveIntegerField(default=0)
    popularity_score = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['popularity_score']),
        ]

    def __str__(self):
        return f"Popularity Metrics for {self.user.profile_name}"