from django.db import models
from django.db.models import Avg, Count, Sum
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    image = CloudinaryField('image', blank=True, null=True, folder="profiles",
                            transformation={"format": "webp", "quality": "auto:eco", "crop": "limit", "width": 1000, "height": 1000})
    popularity_score = models.FloatField(default=0)

    def clean(self):
        super().clean()
        if self.image and self.image.size > 2 * 1024 * 1024:
            raise ValidationError("Profile image must be less than 2MB.")

    @property
    def follower_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    def update_popularity_score(self):
        posts = self.user.posts.all()
        avg_rating = posts.aggregate(Avg('average_rating'))['average_rating__avg'] or 0
        total_ratings = posts.aggregate(total_ratings=Sum('total_ratings'))['total_ratings'] or 0
        follower_count = self.user.followers.count()

        self.popularity_score = (avg_rating * 0.4) + (total_ratings * 0.3) + (follower_count * 0.3)        
        self.save(update_fields=['popularity_score'])
        
    @classmethod
    def update_all_popularity_scores(cls):
        from .tasks import update_all_popularity_scores
        update_all_popularity_scores.delay()

    def __str__(self):
        return f"{self.user.profile_name}'s profile"