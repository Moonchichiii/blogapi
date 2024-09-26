from django.db import models
from django.db.models import Avg, Count
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.fields import GenericRelation
from tags.models import ProfileTag

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = CloudinaryField('image', blank=True, null=True, transformation={"format": "webp", "quality": "auto:eco", "crop": "limit", "width": 2000, "height": 2000})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    average_rating = models.FloatField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    tags = GenericRelation(ProfileTag)

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
        return self.average_rating

    def get_total_ratings(self):
        return self.total_ratings