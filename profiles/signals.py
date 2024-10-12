from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.transaction import atomic
from .models import Profile
from ratings.models import Rating
from followers.models import Follow
from ratings.tasks import update_profile_popularity_score

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update the user profile when a User instance is created or updated."""
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

@receiver(post_save, sender=Rating)
def update_popularity_on_rating(sender, instance, **kwargs):
    """Update profile popularity score when a rating is saved."""
    update_profile_popularity_score.delay(instance.post.author.profile.id)

@receiver(post_save, sender=Follow)
@atomic
def update_follow_counts_on_follow(sender, instance, created, **kwargs):
    """Increment follower count when a follow is created."""
    if created:
        instance.followed.profile.follower_count = F('follower_count') + 1
        instance.followed.profile.save(update_fields=['follower_count'])

@receiver(post_delete, sender=Follow)
@atomic
def update_follow_counts_on_unfollow(sender, instance, **kwargs):
    """Decrement follower count when a follow is deleted."""
    instance.followed.profile.follower_count = F('follower_count') - 1
    instance.followed.profile.save(update_fields=['follower_count'])
