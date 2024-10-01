from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Follow(models.Model):
    """
    Model representing a follow relationship between users.
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='following',
        on_delete=models.CASCADE
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='followers',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.profile_name} follows {self.followed.profile_name}"

@receiver(post_save, sender=Follow)
def update_profile_on_follow(sender, instance, created, **kwargs):
    """
    Signal receiver to update the follower count and popularity score
    when a follow relationship is created.
    """
    if created:
        instance.followed.profile.follower_count += 1
        instance.followed.profile.save()
    instance.followed.profile.update_popularity_score()

@receiver(post_delete, sender=Follow)
def update_profile_on_unfollow(sender, instance, **kwargs):
    """
    Signal receiver to update the follower count and popularity score
    when a follow relationship is deleted.
    """
    instance.followed.profile.follower_count -= 1
    instance.followed.profile.save()
    instance.followed.profile.update_popularity_score()