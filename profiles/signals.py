from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile
from followers.models import Follow


import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        logger.info(f"Profile created for new user: {instance.profile_name}")


@receiver(post_delete, sender=Profile)
def remove_follows_on_profile_delete(sender, instance, **kwargs):
    Follow.objects.filter(follower=instance.user).delete()
    Follow.objects.filter(followed=instance.user).delete()
    logger.info(f"Follows removed for deleted user: {instance.user.profile_name}")