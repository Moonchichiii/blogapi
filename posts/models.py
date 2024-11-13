from django.conf import settings
from django.db import models
from django.db.models import Q
from cloudinary.models import CloudinaryField
from django.db.models import Avg, Count

class Post(models.Model):
    """Represents a user's post with optimized fields and methods.
    Attributes:
        author (ForeignKey): The author of the post, linked to the user model.
        title (CharField): The title of the post.
        content (TextField): The content of the post.
        image (CloudinaryField): An optional image associated with the post.
        created_at (DateTimeField): The timestamp when the post was created.
        updated_at (DateTimeField): The timestamp when the post was last updated.
        is_approved (BooleanField): Indicates if the post is approved.
        average_rating (FloatField): The average rating of the post.
        total_ratings (PositiveIntegerField): The total number of ratings the post has received.
    """
    def __str__(self) -> str:
        """Returns a string representation of the post.
        Returns:
            str: A string showing the author's profile name and the post title.
        """
    def update_rating_statistics(self) -> None:
        """Updates rating statistics using optimized aggregation.
        Aggregates the average rating and total number of ratings, then updates
        the corresponding fields in the post.
        """
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
            models.Index(fields=['average_rating', '-created_at']),
            models.Index(fields=['title']),
        ]
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['title'],
                name='unique_post_title_case_insensitive',
                condition=Q(is_approved=True)
            )
        ]

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