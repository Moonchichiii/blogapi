from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Post
from profiles.models import Profile

@shared_task
def update_post_stats(post_id):
    """
    Update the rating statistics of a post and the popularity score of its author.
    """
    try:
        post = Post.objects.get(id=post_id)
        post.update_rating_statistics()

        profile = Profile.objects.get(user=post.author)
        profile.update_popularity_score()
    except Post.DoesNotExist:
        print(f"Post with ID {post_id} does not exist.")
    except Profile.DoesNotExist:
        print(f"Profile for post author (Post ID: {post_id}) does not exist.")
    except Exception as e:
        print(f"Error updating post stats for post ID {post_id}: {str(e)}")

@shared_task
def send_email_task(subject, message, recipient_list):
    """
    Send an email with the given subject, message, and recipient list.
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
