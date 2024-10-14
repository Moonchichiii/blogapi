from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follow


@receiver(post_save, sender=Follow)
def update_profile_on_follow(sender, instance, created, **kwargs):
    """Update follower count and popularity score when a new follow is created."""
    if created:
        instance.followed.profile.follower_count += 1
        instance.followed.profile.save(update_fields=["follower_count"])
        instance.follower.profile.following_count += 1
        instance.follower.profile.save(update_fields=["following_count"])
        instance.followed.profile.update_popularity_score()


@receiver(post_delete, sender=Follow)
def update_profile_on_unfollow(sender, instance, **kwargs):
    """Update follower count and popularity score when a follow is removed."""
    if instance.followed.profile.follower_count > 0:
        instance.followed.profile.follower_count -= 1
        instance.followed.profile.save(update_fields=["follower_count"])
    if instance.follower.profile.following_count > 0:
        instance.follower.profile.following_count -= 1
        instance.follower.profile.save(update_fields=["following_count"])
    instance.followed.profile.update_popularity_score()
