from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Follow
from notifications.utils import send_notification_task

# Cache Invalidation Helpers

def invalidate_follower_cache(user_id):
    """
    Invalidate cache for the follower list of a user.
    This ensures that stale data is not served after follow/unfollow actions.
    """
    cache_key = f"user_{user_id}_follower_list"
    cache.delete(cache_key)
    print(f"Cache invalidated for user {user_id}'s follower list")

# Follow-related Signals (With Cache Invalidation)

@receiver(post_save, sender=Follow)
def update_profile_on_follow(sender, instance, created, **kwargs):
    """
    Update counts, popularity score, invalidate cache, and send notification on follow.
    Triggered: After a Follow instance is saved.
    """
    if created:
        # Update follower and following counts
        instance.followed.profile.follower_count += 1
        instance.followed.profile.save(update_fields=["follower_count"])
        instance.follower.profile.following_count += 1
        instance.follower.profile.save(update_fields=["following_count"])

        # Update popularity score
        instance.followed.profile.update_popularity_score()

        # Invalidate cache for both followed and follower users
        invalidate_follower_cache(instance.followed.id)
        invalidate_follower_cache(instance.follower.id)

        # Send follow notification
        message = f"{instance.follower.profile_name} started following you."
        send_notification_task.delay(user_id=instance.followed.id, notification_type="Follow", message=message)

@receiver(post_delete, sender=Follow)
def update_profile_on_unfollow(sender, instance, **kwargs):
    """
    Update counts, popularity score, and invalidate cache on unfollow.
    Triggered: After a Follow instance is deleted.
    """
    # Update follower and following counts
    if instance.followed.profile.follower_count > 0:
        instance.followed.profile.follower_count -= 1
        instance.followed.profile.save(update_fields=["follower_count"])
    if instance.follower.profile.following_count > 0:
        instance.follower.profile.following_count -= 1
        instance.follower.profile.save(update_fields=["following_count"])

    # Update popularity score
    instance.followed.profile.update_popularity_score()

    # Invalidate cache for both followed and follower users
    invalidate_follower_cache(instance.followed.id)
    invalidate_follower_cache(instance.follower.id)