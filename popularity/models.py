from django.db import models
from django.conf import settings
from django.db.models import Avg, Count
import logging

logger = logging.getLogger(__name__)

class PopularityMetrics(models.Model):
    """Tracks and calculates user popularity metrics."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='popularity_metrics'
    )
    total_posts = models.PositiveIntegerField(default=0)
    total_ratings_received = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    engagement_score = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['-engagement_score']),
            models.Index(fields=['-average_rating']),
        ]

    def __str__(self):
        return f"Metrics for {self.user.email}"

    def update_metrics(self):
        """Efficient method to update all metrics at once."""
        from posts.models import Post  # Import here to avoid circular import
        
        try:
            posts = Post.objects.filter(author=self.user)
            post_stats = posts.aggregate(
                total_posts=Count('id'),
                total_ratings=Count('ratings'),
                avg_rating=Avg('average_rating')
            )

            self.total_posts = post_stats['total_posts']
            self.total_ratings_received = post_stats['total_ratings']
            self.average_rating = post_stats['avg_rating'] or 0.0
            
            self.engagement_score = (
                (self.average_rating * 0.6) +
                (self.total_posts * 0.2) +
                (self.total_ratings_received * 0.2)
            )
            self.save(update_fields=[
                'total_posts',
                'total_ratings_received',
                'average_rating',
                'engagement_score',
                'last_updated'
            ])
            logger.info(f"Updated metrics for user {self.user.id}: score={self.engagement_score}")
            
        except Exception as e:
            logger.error(f"Error updating metrics for user {self.user.id}: {str(e)}")
            raise
