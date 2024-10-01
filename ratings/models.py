from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from posts.models import Post


class Rating(models.Model):
    """
    Model to represent a rating given by a user to a post.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    post = models.ForeignKey(
        Post,
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
def update_post_rating(sender, instance, **kwargs):
    """
    Signal receiver to update the rating statistics of a post
    whenever a rating is saved or deleted.
    """
    instance.post.update_rating_stats()


@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_profile_popularity(sender, instance, **kwargs):
    """
    Signal receiver to update the popularity score of a user's profile
    whenever a rating is saved or deleted.
    """
    instance.post.author.profile.update_popularity_score()