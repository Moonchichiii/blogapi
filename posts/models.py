from django.db import models
from django.db.models import Avg, Count
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.fields import GenericRelation
from tags.models import ProfileTag
from .messages import STANDARD_MESSAGES
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Post(models.Model):
    """
    Model representing a blog post.
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
        }
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    tags = GenericRelation(ProfileTag)
    slug = models.SlugField(max_length=250, unique=True, blank=True)

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['author']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def update_rating_stats(self):
        stats = self.ratings.aggregate(
            avg_rating=Avg('value'),
            total_ratings=Count('id')
        )
        self.average_rating = stats['avg_rating'] or 0
        self.total_ratings = stats['total_ratings']
        self.save(update_fields=['average_rating', 'total_ratings'])

    def get_average_rating(self):
        if not hasattr(self, '_cached_average_rating'):
            self._cached_average_rating = self.average_rating
        return self._cached_average_rating

    def get_total_ratings(self):
        if not hasattr(self, '_cached_total_ratings'):
            self._cached_total_ratings = self.total_ratings
        return self._cached_total_ratings

    def clean(self):
        if Post.objects.filter(title=self.title).exclude(pk=self.pk).exists():
            raise ValidationError(STANDARD_MESSAGES['POST_DUPLICATE_TITLE']['message'])
        super().clean()
