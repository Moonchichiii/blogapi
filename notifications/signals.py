from django.db.models.signals import post_save
from django.dispatch import receiver
from comments.models import Comment
from ratings.models import Rating
from followers.models import Follow
from tags.models import ProfileTag
from .models import Notification

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        message = f"{instance.follower.profile_name} started following you."
        Notification.objects.create(
            user=instance.followed,
            notification_type="Follow",
            message=message
        )

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.post.author != instance.author:
        message = f"{instance.author.profile_name} commented on your post '{instance.post.title}'."
        Notification.objects.create(
            user=instance.post.author,
            notification_type="Comment",
            message=message
        )

@receiver(post_save, sender=Rating)
def create_rating_notification(sender, instance, created, **kwargs):
    if created and instance.post.author != instance.user:
        message = f"{instance.user.profile_name} rated your post '{instance.post.title}'."
        Notification.objects.create(
            user=instance.post.author,
            notification_type="Rating",
            message=message
        )

@receiver(post_save, sender=ProfileTag)
def create_tag_notification(sender, instance, created, **kwargs):
    if created:
        content_type = instance.content_type.model_class().__name__
        message = f"You were tagged in a {content_type} by {instance.tagger.profile_name}."
        Notification.objects.create(
            user=instance.tagged_user,
            notification_type="Tag",
            message=message
        )