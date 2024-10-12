from celery import shared_task
from .models import Profile

@shared_task
def update_all_popularity_scores():
    profiles = Profile.objects.all().only('id', 'user', 'popularity_score', 'follower_count')
    for profile in profiles:
        profile.update_popularity_score()
    return f"Updated popularity scores for {profiles.count()} profiles"
