from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Count, Sum
from cloudinary.models import CloudinaryField

class Profile(models.Model):
    """
    Model to store user profile information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(max_length=500, blank=True)
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        folder="profiles",
        transformation={
            "format": "webp",
            "quality": "auto:eco",
            "crop": "limit",
            "width": "1000",
            "height": "1000"
        }
    )
    popularity_score = models.FloatField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    tag_count = models.PositiveIntegerField(default=0)

    def clean(self) -> None:
        """
        Custom validation to ensure image size is within limits.
        """
        super().clean()
        if self.image and self.image.size > 2 * 1024 * 1024:
            raise ValidationError("Profile image must be less than 2MB.")

    def update_popularity_score(self) -> None:
        """
        Update the popularity score based on various metrics.
        """
        posts = self.user.posts.all()
        avg_rating = posts.aggregate(Avg('average_rating'))['average_rating__avg'] or 0
        total_ratings = posts.aggregate(Sum('total_ratings'))['total_ratings'] or 0
        comment_count = self.user.comments.count()
        tag_count = self.user.tags.count()
        follower_count = self.follower_count

        self.popularity_score = (
            (avg_rating * 0.3) +
            (total_ratings * 0.2) +
            (comment_count * 0.1) +
            (tag_count * 0.1) +
            (follower_count * 0.3)
        )
        self.save(update_fields=['popularity_score'])

    def update_counts(self) -> None:
        """
        Update follower, following, comment, and tag counts.
        """
        self.follower_count = self.user.followers.count()
        self.following_count = self.user.following.count()
        self.comment_count = self.user.comments.count()
        self.tag_count = self.user.tags.count()
        self.save(
            update_fields=[
                'follower_count',
                'following_count',
                'comment_count',
                'tag_count'
            ]
        )

    def update_rating_statistics(self) -> None:
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

    @classmethod
    def update_all_popularity_scores(cls) -> None:
        """
        Update popularity scores for all profiles asynchronously.
        """
        from .tasks import update_all_popularity_scores
        update_all_popularity_scores.delay()

    def __str__(self) -> str:
        """
        String representation of the Profile model.
        """
        return f"{self.user.profile_name}'s profile"
