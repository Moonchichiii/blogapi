from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Follow
from profiles.models import Profile

def invalidate_follower_cache(user_id):
    cache_key = f"user_{user_id}_follower_list"
    cache.delete(cache_key)
    print(f"Cache invalidated for user_id: {user_id}")

@receiver(post_save, sender=Follow)
def handle_new_follow(sender, instance, created, **kwargs):
    if created:
        print(f"New follow created: {instance.follower.id} -> {instance.followed.id}")
        invalidate_follower_cache(instance.followed.id)
        invalidate_follower_cache(instance.follower.id)

        # Update follower count
        Profile.objects.filter(user=instance.followed).update(
            follower_count=Follow.objects.filter(followed=instance.followed).count()
        )

@receiver(post_delete, sender=Follow)
def handle_unfollow(sender, instance, **kwargs):
    print(f"Follow deleted: {instance.follower.id} -> {instance.followed.id}")
    invalidate_follower_cache(instance.followed.id)
    invalidate_follower_cache(instance.follower.id)

    # Update follower count
    Profile.objects.filter(user=instance.followed).update(
        follower_count=Follow.objects.filter(followed=instance.followed).count()
    )