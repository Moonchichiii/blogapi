from celery import shared_task
from posts.models import Post
from popularity.tasks import aggregate_popularity_score

@shared_task
def update_post_stats(post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.update_rating_statistics()
        aggregate_popularity_score.delay(post.author.id)
    except Post.DoesNotExist:
        print(f"Post with ID {post_id} does not exist.")
    except Exception as e:
        print(f"Error updating post stats for post ID {post_id}: {str(e)}")