from django.db import transaction
from celery import shared_task
from .models import Profile
from popularity.tasks import PopularityMetrics
from popularity.tasks import aggregate_popularity_score

@shared_task
def update_all_popularity_scores():
    """
    Update the popularity scores for all profiles.
    """
    profiles = Profile.objects.all().only("id", "user")

    with transaction.atomic():
        for profile in profiles:
            aggregate_popularity_score.delay(profile.user_id)

    return f"Initiated popularity score updates for {profiles.count()} profiles"