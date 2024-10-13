from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile
from ratings.models import Rating
from ratings.tasks import update_profile_popularity_score

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update the user profile when a User instance is created or updated."""
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

@receiver(post_save, sender=Rating)
def update_popularity_on_rating(sender, instance, **kwargs):
    """Update profile popularity score when a rating is saved."""
    update_profile_popularity_score.delay(instance.post.author.profile.id)
