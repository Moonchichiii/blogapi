import logging
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class NotificationListView(generics.ListAPIView):
    """List all notifications for the authenticated user."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """Return the notifications for the current user."""
        return Notification.objects.filter(user=self.request.user).select_related('user').order_by('-created_at')

class MarkNotificationAsReadView(generics.UpdateAPIView):
    """Mark a specific notification as read."""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        """Mark notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        logger.info(f"Notification {notification.id} marked as read.")
        return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)

class BulkMarkNotificationsAsReadView(generics.UpdateAPIView):
    """Mark all unread notifications for the user as read."""
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        """Bulk mark notifications as read."""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        logger.info(f"All notifications for user {request.user.id} marked as read.")
        return Response({"message": "All notifications marked as read"}, status=status.HTTP_200_OK)