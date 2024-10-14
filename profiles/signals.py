from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile
from ratings.tasks import update_profile_popularity_score
from ratings.models import Rating
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """Create or update a Profile instance after a User is created."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=Rating)
def update_popularity_on_rating(sender, instance, **kwargs):
    """Update profile popularity score when a rating is saved."""
    if instance.post.author.profile:
        update_profile_popularity_score.delay(instance.post.author.profile.id)
