from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Avg, Count

from cloudinary.models import CloudinaryField
from tags.models import ProfileTag


class Post(models.Model):
    """
    Represents a blog post.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        transformation={
            "format": "webp",
            "quality": "auto:eco",
            "crop": "limit",
            "width": 2000,
            "height": 2000
        },
        default='default.webp'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    tags = GenericRelation(ProfileTag)

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['author']),
        ]

    def __str__(self) -> str:
        return str(self.title)

    def update_rating_statistics(self):
        """
        Update the average rating and total ratings for the post.
        """
        rating_stats = self.ratings.aggregate(
            avg_rating=Avg('value'),
            total_ratings=Count('id')
        )
        self.average_rating = rating_stats['avg_rating'] or 0
        self.total_ratings = rating_stats['total_ratings']
        self.save(update_fields=['average_rating', 'total_ratings'])
        self.author.profile.update_popularity_score()
