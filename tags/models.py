from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ProfileTag(models.Model):
    """
    Represents a tag on a user's profile.
    """
    tagged_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags'
    )
    tagger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags_created'
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tagged_user', 'content_type', 'object_id')

    def __str__(self) -> str:
        """
        Returns a string representation of the ProfileTag instance.
        """
        return f"{self.tagger.profile_name} tagged {self.tagged_user.profile_name} in {self.content_object}"