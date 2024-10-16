import logging
from django.db import transaction
from celery import shared_task
from .models import Profile
from popularity.tasks import aggregate_popularity_score

logger = logging.getLogger(__name__)

@shared_task
def update_all_popularity_scores():
    profiles = Profile.objects.all().only("id", "user")

    with transaction.atomic():
        for profile in profiles:
            aggregate_popularity_score.delay(profile.user_id)

    logger.info(f"Initiated popularity score updates for {profiles.count()} profiles")
    return f"Initiated popularity score updates for {profiles.count()} profiles"