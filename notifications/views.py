from django.utils import timezone
from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer




from django.utils.decorators import method_decorator
from django.views.decorators.async_unsafe import async_unsafe

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(async_unsafe)
    async def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('user')

class MarkNotificationAsReadView(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return super().update(request, *args, **kwargs)

class BulkMarkNotificationsAsReadView(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({"message": "All notifications marked as read"}, status=status.HTTP_200_OK)