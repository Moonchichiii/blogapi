from celery import shared_task
from .models import Post

@shared_task
def update_post_stats(post_id):
    """
    Update the rating statistics of a post.

    Args:
        post_id (int): The ID of the post to update.
    """
    try:
        post = Post.objects.get(id=post_id)
        post.update_rating_statistics()
    except Post.DoesNotExist:
        pass
    except Exception:
        pass
