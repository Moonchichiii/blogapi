from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Rating
from popularity.tasks import aggregate_popularity_score

@receiver(post_save, sender=Rating)
def update_popularity_on_rating(sender, instance, **kwargs):
    aggregate_popularity_score.delay(instance.post.author.id)