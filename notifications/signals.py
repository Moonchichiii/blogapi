from django.db.models.signals import post_save
from django.dispatch import receiver
from followers.models import Follow
from comments.models import Comment
from ratings.models import Rating
from .models import Notification
from .tasks import send_notification_task


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a user is followed.
    """
    if created:
        message = f"{instance.follower.profile_name} followed you."
        send_notification_task.delay(instance.followed.id, "Follow", message)


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a comment is made on a user's post.
    """
    if created and instance.post.author != instance.author:
        message = f"{instance.author.profile_name} commented on your post '{instance.post.title}'."
        send_notification_task.delay(instance.post.author.id, "Comment", message)


@receiver(post_save, sender=Rating)
def create_rating_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a post is rated by a user.
    """
    if created and instance.post.author != instance.user:
        message = (
            f"{instance.user.profile_name} rated your post '{instance.post.title}'."
        )
        send_notification_task.delay(instance.post.author.id, "Rating", message)
