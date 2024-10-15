from celery import shared_task
from followers.models import Follow
from notifications.models import Notification

@shared_task
def send_notification_task(user_id, notification_type, message):
    """Create a notification asynchronously."""
    Notification.objects.create(
        user_id=user_id, notification_type=notification_type, message=message
    )

@shared_task
def remove_follows_for_user(user_id):
    Follow.objects.filter(follower_id=user_id).delete()
    Follow.objects.filter(followed_id=user_id).delete()
