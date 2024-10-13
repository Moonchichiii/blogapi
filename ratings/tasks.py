from celery import shared_task
from posts.models import Post
from profiles.models import Profile

@shared_task
def update_post_stats(post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.update_rating_statistics()       
        
        update_profile_popularity_score.delay(post.author.profile.id)
    except Post.DoesNotExist:
        print(f"Post with ID {post_id} does not exist.")
    except Exception as e:
        print(f"Error updating post stats for post ID {post_id}: {str(e)}")

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
    except Exception as e:
        print(f"Error updating profile popularity score for profile ID {profile_id}: {str(e)}")