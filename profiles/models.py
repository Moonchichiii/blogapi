from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg
from cloudinary.models import CloudinaryField

class Profile(models.Model):
    """
    Profile model to store user profile information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(max_length=500, blank=True)
    image = CloudinaryField(
        'image', blank=True, null=True,
        folder="profiles",
        transformation={
            "format": "webp",
            "quality": "auto:eco",
            "crop": "limit",
            "width": "1000",
            "height": "1000"
        }
    )
    popularity_score = models.FloatField(default=0, db_index=True)
    follower_count = models.PositiveIntegerField(default=0, db_index=True)
    following_count = models.PositiveIntegerField(default=0)

    def update_popularity_score(self):
        """
        Update the popularity score based on average post rating and follower count.
        """
        avg_rating = self.user.posts.aggregate(
            Avg('average_rating')
        )['average_rating__avg'] or 0
        self.popularity_score = (avg_rating * 0.5) + (self.follower_count * 0.3)
        self.save(update_fields=['popularity_score'])

    def update_counts(self):
        """
        Update follower and following counts.
        """
        self.follower_count = self.user.followers.count()
        self.following_count = self.user.following.count()
        self.save(update_fields=['follower_count', 'following_count'])