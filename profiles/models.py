from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    image = CloudinaryField('image', blank=True, null=True, 
                            folder="profiles",  # Store profile images in a separate folder
                            transformation={
                                "format": "webp",  # Ensure the format is WebP
                                "quality": "auto:eco",  # Auto-adjust quality for optimization
                                "crop": "limit",  # Limit the dimensions
                                "width": 1000,  # Set max width
                                "height": 1000  # Set max height
                            })

    def clean(self):
        super().clean()
        if self.image and self.image.size > 2 * 1024 * 1024:  # Size limit check (2MB)
            raise ValidationError("Profile image must be less than 2MB.")

    @property
    def follower_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def popularity_score(self):
        posts = self.user.posts.all()
        avg_rating = posts.aggregate(Avg('ratings__value'))['ratings__value__avg'] or 0
        total_ratings = posts.aggregate(total_ratings=Count('ratings'))['total_ratings'] or 0
        follower_count = self.follower_count
        score = (avg_rating * 0.4) + (total_ratings * 0.3) + (follower_count * 0.3)
        return round(score, 2)

    def __str__(self):
        return f"{self.user.profile_name}'s profile"
