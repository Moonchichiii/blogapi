import logging
from celery import shared_task
from posts.models import Post
from popularity.tasks import aggregate_popularity_score

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def update_post_stats(self, post_id):
    logger.info(f"Task {self.request.id}: Starting update_post_stats for post {post_id}")
    try:
        post = Post.objects.get(id=post_id)
        logger.info(f"Task {self.request.id}: Found post {post_id}")
        
        old_rating = post.average_rating
        logger.info(f"Task {self.request.id}: Old rating: {old_rating}")
        
        post.update_rating_statistics()
        logger.info(f"Task {self.request.id}: Updated rating statistics")
        
        post.refresh_from_db()
        new_rating = post.average_rating
        logger.info(f"Task {self.request.id}: New rating: {new_rating}")
        
        aggregate_popularity_score.delay(post.author.id)
        logger.info(f"Task {self.request.id}: Triggered aggregate_popularity_score for user {post.author.id}")
        
        result = f"Updated stats for post {post_id}. New rating: {new_rating}"
        logger.info(f"Task {self.request.id}: Completed. Returning result: {result}")
        return result
    except Post.DoesNotExist:
        logger.warning(f"Task {self.request.id}: Post with ID {post_id} does not exist.")
        return f"Post with ID {post_id} does not exist."
    except Exception as e:
        logger.error(f"Task {self.request.id}: Error updating stats for post {post_id}: {str(e)}")
        return f"Error updating stats for post {post_id}: {str(e)}"
    
    
