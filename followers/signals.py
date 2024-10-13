from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follow

@receiver(post_save, sender=Follow)
def update_profile_on_follow(sender, instance, created, **kwargs):
    """Increment follower and following counts after a follow is created."""
    if created:
        instance.followed.profile.follower_count += 1
        instance.followed.profile.save(update_fields=['follower_count'])
        instance.follower.profile.following_count += 1
        instance.follower.profile.save(update_fields=['following_count'])

@receiver(post_delete, sender=Follow)
def update_profile_on_unfollow(sender, instance, **kwargs):
    """Decrement follower and following counts after a follow is deleted."""
    instance.followed.profile.follower_count -= 1
    instance.followed.profile.save(update_fields=['follower_count'])
    instance.follower.profile.following_count -= 1
    instance.follower.profile.save(update_fields=['following_count'])
