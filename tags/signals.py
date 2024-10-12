from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import ProfileTag, Post, Comment

@receiver(post_delete, sender=Post)
@receiver(post_delete, sender=Comment)
def delete_tags_on_content_delete(sender, instance, **kwargs):
    """Delete related tags when a Post or Comment is deleted."""
    ProfileTag.objects.filter(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id
    ).delete()
