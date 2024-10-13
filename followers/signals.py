from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follow

@receiver(post_save, sender=Follow)
def update_profile_on_follow(sender, instance, created, **kwargs):
    """Update follower count and popularity score when a new follow is created."""
    if created:
        instance.followed.profile.follower_count += 1
        instance.followed.profile.update_popularity_score()

@receiver(post_delete, sender=Follow)
def update_profile_on_unfollow(sender, instance, **kwargs):
    """Update follower count and popularity score when a follow is removed."""
    instance.followed.profile.follower_count -= 1
    instance.followed.profile.update_popularity_score()