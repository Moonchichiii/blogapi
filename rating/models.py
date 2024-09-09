from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from posts.models import Post

class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='ratings')
    value = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.profile_name} rated {self.post.title} {self.value} stars"