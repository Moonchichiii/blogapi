from celery import shared_task
from .models import Notification
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProfileTag
from notifications.tasks import send_notification_task


@shared_task
def send_notification_task(user_id, notification_type, message):
    """Create a notification asynchronously."""
    Notification.objects.create(
        user_id=user_id, notification_type=notification_type, message=message
    )



@receiver(post_save, sender=ProfileTag)
def notify_tagged_user(sender, instance, created, **kwargs):
    """Send notification when a user is tagged in a post."""
    if created:
        message = f"You were tagged in a post by {instance.tagger.profile_name}."
        send_notification_task.delay(
            user_id=instance.tagged_user.id,
            notification_type="Tag",
            message=message
        )