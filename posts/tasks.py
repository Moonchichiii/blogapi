import logging
from celery import shared_task
from .models import Post

logger = logging.getLogger(__name__)

@shared_task
def update_post_stats(post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.update_rating_stats()
        logger.info(f"Stats updated for post {post_id}")
    except Post.DoesNotExist:
        logger.error(f"Post {post_id} not found")
    except Exception as e:
        logger.error(f"Unexpected error in update_post_stats: {str(e)}")
