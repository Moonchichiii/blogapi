from celery import shared_task
from profiles.models import Profile

@shared_task
def update_profile_popularity_score(profile_id):
    """
    Update the popularity score of a profile based on ratings.
    """
    try:
        profile = Profile.objects.get(id=profile_id)
        profile.update_popularity_score()
    except Profile.DoesNotExist:
        print(f"Profile with id {profile_id} does not exist.")
