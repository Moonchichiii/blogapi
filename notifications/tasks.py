from celery import shared_task
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from tags.models import ProfileTag

# Tasks
@shared_task
def send_notification_task(user_id, notification_type, message):
    """Create a notification asynchronously."""
    Notification.objects.create(
        user_id=user_id, notification_type=notification_type, message=message
    )

# Signal Handlers

# Tagging-related Signals
@receiver(post_save, sender=ProfileTag)
def notify_tagged_user(sender, instance, created, **kwargs):
    """
    Send notification when a user is tagged in a post.
   
    Triggered: After a ProfileTag instance is created.
    """
    if created:
        message = f"You were tagged in a post by {instance.tagger.profile_name}."
        send_notification_task.delay(
            user_id=instance.tagged_user.id,
            notification_type="Tag",
            message=message
        )
