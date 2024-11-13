from django.db import models
from django.conf import settings
from django.db.models import Avg, Count

class PopularityMetrics(models.Model):
    """Simplified popularity metrics with focused scoring."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='popularity_metrics'
    )
    post_count = models.PositiveIntegerField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    popularity_score = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['-popularity_score'])]

    def __str__(self):
        return f"Metrics for {self.user.profile_name}"

    def update_metrics(self):
        """Update metrics using efficient queries."""
        from posts.models import Post
        
        posts = Post.objects.filter(author=self.user)
        post_stats = posts.aggregate(
            count=Count('id'),
            avg_rating=Avg('average_rating'),
            total_ratings=Sum('total_ratings')
        )

        self.post_count = post_stats['count']
        self.average_rating = post_stats['avg_rating'] or 0
        self.total_ratings = post_stats['total_ratings'] or 0
        
        # Simplified scoring formula
        self.popularity_score = (
            (self.average_rating * 0.6) +
            (self.post_count * 0.4)
        )
        
        self.save()