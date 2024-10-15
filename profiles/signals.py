from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from followers.models import Follow
from .models import Profile
from popularity.models import PopularityMetrics 
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Signal to create or update Profile when a User is created
@receiver(post_save, sender=User)
def create_or_update_user_related_models(sender, instance, created, **kwargs):
    """
    Signal: Create a Profile and PopularityMetrics instance when a User is created.
    """
    if created:
        Profile.objects.create(user=instance)
        PopularityMetrics.objects.create(user=instance)
        logger.info(f"Profile and PopularityMetrics created for new user: {instance.profile_name}")

# Signal to remove follow relationships when a Profile is deleted
@receiver(post_delete, sender=Profile)
def remove_follows_on_profile_delete(sender, instance, **kwargs):
    """
    Signal: Remove follow relationships when a Profile is deleted.
    """
    Follow.objects.filter(follower=instance.user).delete()
    Follow.objects.filter(followed=instance.user).delete()
    logger.info(f"Follows removed for deleted user: {instance.user.profile_name}")

# Signal to update follower count when a user is followed
@receiver(post_save, sender=Follow)
def update_follower_count_on_follow(sender, instance, created, **kwargs):
    """
    Signal: Update follower count in Profile when a user is followed.
    """
    if created:
        followed_profile = Profile.objects.get(user=instance.followed)
        followed_profile.follower_count = Follow.objects.filter(followed=instance.followed).count()
        followed_profile.save()
        logger.info(f"Follower count updated for user: {instance.followed.profile_name}")

# Signal to update follower count when a user is unfollowed
@receiver(post_delete, sender=Follow)
def update_follower_count_on_unfollow(sender, instance, **kwargs):
    """
    Signal: Update follower count in Profile when a user is unfollowed.
    """
    followed_profile = Profile.objects.get(user=instance.followed)
    followed_profile.follower_count = Follow.objects.filter(followed=instance.followed).count()
    followed_profile.save()
    logger.info(f"Follower count updated for user: {instance.followed.profile_name}")
