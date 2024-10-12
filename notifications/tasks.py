from celery import shared_task
from .models import Notification

@shared_task
def send_notification_task(user_id, notification_type, message):
    """Create a notification asynchronously."""
    Notification.objects.create(
        user_id=user_id,
        notification_type=notification_type,
        message=message
    )
