from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=50)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.profile_name} - {self.notification_type}"
   
    def save(self, *args, **kwargs):
        if not get_user_model().objects.filter(id=self.user_id).exists():
            raise get_user_model().DoesNotExist("User does not exist")
        super().save(*args, **kwargs)

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type', '-created_at']),
        ]
        ordering = ['-created_at']