from django.db import models
from django.db.models import Avg
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation
from tags.models import ProfileTag

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = CloudinaryField(
        'image', blank=True, null=True,
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
    tags = GenericRelation(ProfileTag)

            
    @property
    def average_rating(self):
        return self.ratings.aggregate(Avg('value'))['value__avg']

    @property
    def total_ratings(self):
        return self.ratings.count()

    def __str__(self):
        return self.title