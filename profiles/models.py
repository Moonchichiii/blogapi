from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    profile_name = models.CharField(max_length=255, unique=True, db_index=True)
    bio = models.TextField(max_length=500, blank=True)
    image = CloudinaryField(
        "image",
        blank=True,
        null=True,
        folder="profiles",
        transformation={
            "format": "webp",
            "quality": "auto:eco",
            "crop": "limit",
            "width": "1000",
            "height": "1000",
        },
    )    
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['profile_name']),
            models.Index(fields=['user', 'profile_name']),
        ]