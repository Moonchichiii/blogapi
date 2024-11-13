from django.db.models.signals import post_save
from django.dispatch import receiver
from comments.models import Comment
from ratings.models import Rating
from followers.models import Follow
from .tasks import send_notification_task

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a user starts following another user.
    """
    if created:
        message = f"{instance.follower.profile_name} started following you."
        send_notification_task.delay(
            user_id=instance.followed.id,
            notification_type="Follow",
            message=message
        )
@receiver(post_save, sender=Rating)
def notify_post_rating(sender, instance, created, **kwargs):
    """Notify authors of new ratings."""
    if created and instance.post.author != instance.user:
        send_notification_task.delay(
            user_id=instance.post.author.id,
            notification_type="Rating",
            message=f"{instance.user.profile_name} rated your post '{instance.post.title}'"
        )

@receiver(post_save, sender=Comment)
def notify_post_comment(sender, instance, created, **kwargs):
    """Notify authors of new comments."""
    if created and instance.post.author != instance.author:
        send_notification_task.delay(
            user_id=instance.post.author.id,
            notification_type="Comment",
            message=f"{instance.author.profile_name} commented on '{instance.post.title}'"
        )