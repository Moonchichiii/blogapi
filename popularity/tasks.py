from celery import shared_task
from django.db import transaction
from django.db.models import Avg
from .models import PopularityMetrics
from posts.models import Post
from profiles.models import Profile
import logging

logger = logging.getLogger(__name__)

@shared_task
def aggregate_popularity_score(user_id):
    try:
        with transaction.atomic():
            metrics, created = PopularityMetrics.objects.select_for_update().get_or_create(user_id=user_id)
            
            try:
                user_posts = Post.objects.filter(author_id=user_id)
                metrics.post_count = user_posts.count()
                metrics.average_post_rating = user_posts.aggregate(Avg('average_rating'))['average_rating__avg'] or 0
            except Exception as e:
                logger.error(f"Error fetching posts for user {user_id}: {str(e)}", exc_info=True)
                metrics.post_count = 0
                metrics.average_post_rating = 0

            try:
                profile = Profile.objects.get(user_id=user_id)
                metrics.follower_count = profile.follower_count
            except Profile.DoesNotExist:
                logger.error(f"Profile not found for user {user_id}. Setting follower count to 0.")
                metrics.follower_count = 0

            logger.info(f"Post count for user {user_id}: {metrics.post_count}, Average rating: {metrics.average_post_rating}, Follower count: {metrics.follower_count}")

            metrics.popularity_score = (
                (metrics.average_post_rating * 0.6) +
                (metrics.post_count * 0.3) +
                (metrics.follower_count * 0.1)
            )
            logger.info(f"Calculated popularity score for user {user_id}: {metrics.popularity_score}")

            metrics.save()

        return f"Updated popularity score for user {user_id}"
    except Exception as e:
        logger.error(f"Error updating popularity score for user {user_id}: {str(e)}", exc_info=True)
        return f"Error updating popularity score for user {user_id}: {str(e)}"