from django.urls import path
from .views import NotificationListView, MarkNotificationAsReadView, BulkMarkNotificationsAsReadView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:pk>/mark-read/", MarkNotificationAsReadView.as_view(), name="mark-notification-read"),
    path("notifications/mark-all-read/", BulkMarkNotificationsAsReadView.as_view(), name="bulk-mark-notifications-read"),
]
