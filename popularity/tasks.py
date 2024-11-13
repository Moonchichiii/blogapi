from celery import shared_task
from django.db import transaction
from posts.models import Post
import logging

logger = logging.getLogger(__name__)

@shared_task
def aggregate_popularity_score(user_id: int) -> str:
    """Aggregate and update the popularity score for a given user."""
    from .models import PopularityMetrics  
    
    logger.debug(f"Starting popularity score aggregation for user {user_id}")
    
    try:
        with transaction.atomic():
            metrics, created = PopularityMetrics.objects.select_for_update().get_or_create(
                user_id=user_id
            )
            metrics.update_metrics()
            return f"Updated metrics for user {user_id}"
    except Exception as e:
        logger.error(f"Error updating metrics for user {user_id}: {str(e)}", exc_info=True)
        raise

@shared_task
def update_all_popularity_scores() -> str:
    """Batch task to update popularity scores for all users."""
    try:
        user_ids = Post.objects.values_list('author_id', flat=True).distinct()
        logger.info(f"Starting batch update for {len(user_ids)} users")
        
        for user_id in user_ids:
            aggregate_popularity_score.delay(user_id)
            
        return f"Queued updates for {len(user_ids)} users"
        
    except Exception as e:
        logger.error(f"Error in batch popularity update: {str(e)}", exc_info=True)
        raise
