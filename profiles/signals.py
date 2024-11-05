from django.db.models.signals import post_save, post_delete
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from followers.models import Follow
from .models import Profile
from popularity.models import PopularityMetrics
from popularity.tasks import aggregate_popularity_score
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_related_models(sender, instance, created, **kwargs):
    if created:
        with transaction.atomic():
            try:
                # Check if PopularityMetrics already exists
                if not hasattr(instance, 'popularity_metrics'):
                    PopularityMetrics.objects.create(user=instance)
                    logger.info(f"PopularityMetrics created for user {instance.email}")
                else:
                    logger.info(f"PopularityMetrics already exists for user {instance.email}")
            except Exception as e:
                logger.error(f"Error creating metrics for user {instance.email}: {str(e)}")
                raise
            
@receiver(post_delete, sender=Profile)
def remove_follows_on_profile_delete(sender, instance, **kwargs):
    Follow.objects.filter(follower=instance.user).delete()
    Follow.objects.filter(followed=instance.user).delete()
    logger.info(f"Follows removed for deleted user: {instance.user.profile_name}")

@receiver(post_save, sender=Follow)
def update_follower_count_on_follow(sender, instance, created, **kwargs):
    if created:
        followed_profile = Profile.objects.get(user=instance.followed)
        followed_profile.follower_count = Follow.objects.filter(followed=instance.followed).count()
        followed_profile.save()
        logger.info(f"Follower count updated for user: {instance.followed.profile_name}")
        aggregate_popularity_score.delay(instance.followed.id)

@receiver(post_delete, sender=Follow)
def update_follower_count_on_unfollow(sender, instance, **kwargs):
    try:
        followed_profile = Profile.objects.get(user=instance.followed)
        followed_profile.follower_count = Follow.objects.filter(followed=instance.followed).count()
        followed_profile.save()
    except Profile.DoesNotExist:
        pass