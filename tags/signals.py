from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProfileTag
from notifications.tasks import send_notification_task

@receiver(post_save, sender=ProfileTag)
def create_tag_notification(sender, instance, created, **kwargs):
    if created:
        content_type = instance.content_type.model_class().__name__
        message = f'You were tagged in a {content_type} by {instance.tagger.profile_name}.'
        send_notification_task.delay(
            user_id=instance.tagged_user.id,
            notification_type="Tag",
            message=message
        )