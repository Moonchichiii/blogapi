from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification
from posts.models import Post
from comments.models import Comment
from followers.models import Follow

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email="user1@example.com", profile_name="user1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", profile_name="user2", password="testpass123"
        )
        self.client.force_authenticate(user=self.user1)

    def test_follow_notification(self):
        Follow.objects.create(follower=self.user2, followed=self.user1)
        notifications = Notification.objects.filter(
            user=self.user1, notification_type="Follow"
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_comment_notification(self):
        post = Post.objects.create(
            author=self.user1, title="Test Post", content="Test Content"
        )
        Comment.objects.create(post=post, author=self.user2, content="Test Comment")
        notifications = Notification.objects.filter(
            user=self.user1, notification_type="Comment"
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_rating_notification(self):
        post = Post.objects.create(
            author=self.user1, title="Test Post", content="Test Content"
        )
        post.ratings.create(user=self.user2, value=5)
        notifications = Notification.objects.filter(
            user=self.user1, notification_type="Rating"
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_list_notifications(self):
        Notification.objects.create(
            user=self.user1, notification_type="Test", message="Test Notification"
        )
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_mark_notification_as_read(self):
        notification = Notification.objects.create(
            user=self.user1, notification_type="Test", message="Test Notification"
        )
        url = reverse("mark-notification-read", kwargs={"pk": notification.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
