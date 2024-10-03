from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Remove this import
# from posts.models import Post

class Rating(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    post = models.ForeignKey(
        'posts.Post',  # Referencing Post lazily
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post', 'value']),
        ]

    def __str__(self):
        return f"{self.user.profile_name} rated {self.post.title} {self.value} stars"


@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_post_stats(sender, instance, **kwargs):
    # Import Post lazily within the function to avoid circular import
    from posts.models import Post
    from posts.tasks import update_post_stats
    update_post_stats.delay(instance.post.id)
