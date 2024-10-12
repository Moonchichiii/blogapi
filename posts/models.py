from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Avg, Count

from cloudinary.models import CloudinaryField
from tags.models import ProfileTag


from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField

class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        db_index=True
    )
    title = models.CharField(max_length=200, db_index=True)
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
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)

    def update_rating_statistics(self):
        """
        Update the average rating and total ratings for the post.
        """
        rating_stats = self.ratings.aggregate(
            avg_rating=models.Avg('value'),
            total_ratings=models.Count('id')
        )
        self.average_rating = rating_stats['avg_rating'] or 0
        self.total_ratings = rating_stats['total_ratings']
        self.save(update_fields=['average_rating', 'total_ratings'])
        self.author.profile.update_popularity_score()
