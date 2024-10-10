from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile
from ratings.models import Rating

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create or update the user profile when a User instance is created or updated.
    """
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_profile_on_rating_change(sender, instance, **kwargs):
    """
    Update the author's profile popularity score when a Rating instance is saved or deleted.
    """
    instance.post.author.profile.update_popularity_score()
