from django.db import models, connection
from django.db.models import Avg, Count
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.fields import GenericRelation
from tags.models import ProfileTag
from django.core.exceptions import ValidationError

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
        self.author.profile.update_popularity_score()

    @staticmethod
    def explain_query():
        """
        Explain the SQL query for performance analysis.
        """
        qs = Post.objects.filter(is_approved=True).order_by('-created_at')
        sql, params = qs.query.sql_with_params()

        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN {sql}", params)
            for row in cursor.fetchall():
                print(row)
