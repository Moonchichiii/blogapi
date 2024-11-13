from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField
from django.db.models import Avg, Count

class Post(models.Model):
    """Represents a user's post with optimized fields and methods."""
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        db_index=True
    )
    title = models.CharField(max_length=200, db_index=True)
    content = models.TextField()
    image = CloudinaryField(
        "image",
        blank=True,
        null=True,
        transformation={
            "format": "webp",
            "quality": "auto:eco",
            "crop": "limit",
            "width": 2000,
            "height": 2000,
        },
        default="default.webp",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', 'is_approved']),
            models.Index(fields=['average_rating']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.profile_name}: {self.title}"

    def update_rating_statistics(self):
        """Updates rating statistics using optimized aggregation."""
        stats = self.ratings.aggregate(
            avg=Avg('value'),
            total=Count('id')
        )
        self.average_rating = stats['avg'] or 0
        self.total_ratings = stats['total']
        self.save(update_fields=['average_rating', 'total_ratings'])