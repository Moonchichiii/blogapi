from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Rating

@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_post_and_profile_stats(sender, instance, **kwargs):
    """Update post stats and profile score upon rating changes."""
    instance.post.update_rating_statistics()
    instance.post.author.profile.update_popularity_score()
