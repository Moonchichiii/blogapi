from celery import shared_task
from django.db import transaction
from django.db.models import Avg
from .models import PopularityMetrics
from posts.models import Post

@shared_task
def aggregate_popularity_score(user_id):
    try:
        with transaction.atomic():
            metrics, created = PopularityMetrics.objects.select_for_update().get_or_create(user_id=user_id)
            
            # Update follower count
            metrics.follower_count = metrics.user.followers.count()
            
            # Update post statistics
            user_posts = Post.objects.filter(author_id=user_id)
            metrics.post_count = user_posts.count()
            metrics.average_post_rating = user_posts.aggregate(Avg('average_rating'))['average_rating__avg'] or 0
            
            # Calculate popularity score (adjust formula as needed)
            metrics.popularity_score = (
                (metrics.follower_count * 0.4) + 
                (metrics.average_post_rating * 0.4) + 
                (metrics.post_count * 0.2)
            )
            
            metrics.save()
        
        return f"Updated popularity score for user {user_id}"
    except Exception as e:
        return f"Error updating popularity score for user {user_id}: {str(e)}"