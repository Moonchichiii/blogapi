from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from popularity.tasks import aggregate_popularity_score

@receiver(post_save, sender=Post)
def update_popularity_on_post_change(sender, instance, **kwargs):
    aggregate_popularity_score.delay(instance.author.id)