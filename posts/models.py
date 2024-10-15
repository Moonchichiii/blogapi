from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField
from django.db.models import Avg, Count
from tags.models import ProfileTag

class Post(models.Model):
    """Represents a user's post."""

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
    tags = models.ManyToManyField(ProfileTag, related_name="posts", blank=True)

    def update_rating_statistics(self):
        """Updates average rating and total number of ratings."""
        rating_stats = self.ratings.aggregate(
            avg_rating=Avg("value"), total_ratings=Count("id")
        )
        self.average_rating = rating_stats["avg_rating"] or 0
        self.total_ratings = rating_stats["total_ratings"]
        self.save(update_fields=["average_rating", "total_ratings"])

    def __str__(self):
        """Returns a string representation of the post."""
        return f"Post by {self.author.profile_name}: {self.title}"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "created_at"]),
            models.Index(fields=["is_approved"]),
        ]
