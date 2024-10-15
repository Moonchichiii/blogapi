from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Follow
from popularity.tasks import aggregate_popularity_score
from notifications.utils import send_notification_task


def invalidate_follower_cache(user_id):
    cache_key = f"user_{user_id}_follower_list"
    cache.delete(cache_key)

@receiver(post_save, sender=Follow)
def update_profile_on_follow(sender, instance, created, **kwargs):
    if created:
        instance.followed.profile.follower_count += 1
        instance.followed.profile.save(update_fields=["follower_count"])

        instance.follower.profile.following_count += 1
        instance.follower.profile.save(update_fields=["following_count"])

        
        invalidate_follower_cache(instance.followed.id)
        invalidate_follower_cache(instance.follower.id)

        message = f"{instance.follower.profile_name} started following you."
        send_notification_task.delay(user_id=instance.followed.id, notification_type="Follow", message=message)

@receiver(post_delete, sender=Follow)
def update_profile_on_unfollow(sender, instance, **kwargs):
    if instance.followed.profile.follower_count > 0:
        instance.followed.profile.follower_count -= 1
        instance.followed.profile.save(update_fields=["follower_count"])

    if instance.follower.profile.following_count > 0:
        instance.follower.profile.following_count -= 1
        instance.follower.profile.save(update_fields=["following_count"])
    
    invalidate_follower_cache(instance.followed.id)
    invalidate_follower_cache(instance.follower.id)



@receiver(post_save, sender=Follow)
@receiver(post_delete, sender=Follow)
def update_popularity_on_follow_change(sender, instance, **kwargs):
    aggregate_popularity_score.delay(instance.followed.id)