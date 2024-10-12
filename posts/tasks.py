from celery import shared_task
import logging
from .models import Post

logger = logging.getLogger(__name__)

@shared_task
def update_post_stats(post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.update_rating_statistics()
    except Post.DoesNotExist:
        logger.error(f"Post with ID {post_id} does not exist.")
    except Exception as e:
        logger.error(f"Error updating post stats for post ID {post_id}: {str(e)}")

@shared_task
def send_email_task(subject, message, recipient_list):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
