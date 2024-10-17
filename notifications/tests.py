from django.utils import timezone
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status
from .models import Notification
from posts.models import Post
from comments.models import Comment
from followers.models import Follow
from ratings.models import Rating
from tags.models import ProfileTag
from notifications.tasks import send_notification_task
from django.core.cache import cache

User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(email="user1@example.com", profile_name="user1", password="testpass123")
        self.user2 = User.objects.create_user(email="user2@example.com", profile_name="user2", password="testpass123")
        self.client.force_authenticate(user=self.user1)

    def tearDown(self):
        Notification.objects.all().delete()
        User.objects.all().delete()
        self.client.force_authenticate(user=None)
        cache.clear()

    def test_follow_notification(self):
        """Test follow notification"""
        with patch('notifications.tasks.send_notification_task.delay') as mock_task:
            Follow.objects.create(follower=self.user2, followed=self.user1)
            mock_task.assert_called_once_with(
                user_id=self.user1.id,
                notification_type="Follow",
                message=f"{self.user2.profile_name} started following you."
            )
        send_notification_task(self.user1.id, "Follow", f"{self.user2.profile_name} started following you.")
        notifications = Notification.objects.filter(user=self.user1, notification_type="Follow")
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_comment_notification(self):
        """Test comment notification"""
        post = Post.objects.create(author=self.user1, title="Test Post", content="Test Content")
        with patch('notifications.tasks.send_notification_task.delay') as mock_task:
            Comment.objects.create(post=post, author=self.user2, content="Test Comment")
            mock_task.assert_called_once_with(
                user_id=post.author.id,
                notification_type="Comment",
                message=f"{self.user2.profile_name} commented on your post '{post.title}'."
            )
        send_notification_task(post.author.id, "Comment", f"{self.user2.profile_name} commented on your post '{post.title}'.")
        notifications = Notification.objects.filter(user=self.user1, notification_type="Comment")
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_rating_notification(self):
        """Test rating notification"""
        Notification.objects.all().delete()
        post = Post.objects.create(author=self.user1, title="Test Post", content="Test Content")
        with patch('notifications.tasks.send_notification_task.delay') as mock_task:
            Rating.objects.create(post=post, user=self.user2, value=5)
            mock_task.assert_called_once_with(
                user_id=post.author.id,
                notification_type="Rating",
                message=f"{self.user2.profile_name} rated your post '{post.title}'."
            )
        send_notification_task(post.author.id, "Rating", f"{self.user2.profile_name} rated your post '{post.title}'.")
        notifications = Notification.objects.filter(user=self.user1, notification_type="Rating")
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_list_notifications(self):
        Notification.objects.all().delete()
        """Test list notifications"""
        for i in range(15):
            Notification.objects.create(user=self.user1, notification_type="Test", message=f"Test Notification {i}")
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)

    def test_mark_notification_as_read(self):
        """Test mark notification as read"""
        notification = Notification.objects.create(user=self.user1, notification_type="Test", message="Test Notification")
        url = reverse("mark-notification-read", kwargs={"pk": notification.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_tag_notification(self):
        """Test tag notification"""
        post = Post.objects.create(author=self.user2, title="Test Post", content="Test Content")
        content_type = ContentType.objects.get_for_model(Post)
        with patch('notifications.tasks.send_notification_task.delay') as mock_task:
            ProfileTag.objects.create(tagged_user=self.user1, tagger=self.user2, content_type=content_type, object_id=post.id)
            mock_task.assert_called_once_with(
                user_id=self.user1.id,
                notification_type="Tag",
                message=f"You were tagged in a Post by {self.user2.profile_name}."
            )
        send_notification_task(self.user1.id, "Tag", f"You were tagged in a Post by {self.user2.profile_name}.")
        notifications = Notification.objects.filter(user=self.user1, notification_type="Tag")
        self.assertEqual(notifications.count(), 1)
        self.assertIn(self.user2.profile_name, notifications.first().message)

    def test_notification_pagination(self):
        """Test notification pagination"""
        Notification.objects.all().delete()
        for i in range(25):
            Notification.objects.create(user=self.user1, notification_type="Test", message=f"Test Notification {i}")
        url = reverse("notification-list")
        response = self.client.get(f"{url}?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 25)

    def test_notification_ordering(self):
        """Test notification ordering"""
        Notification.objects.all().delete()
        old_notification = Notification.objects.create(
            user=self.user1,
            notification_type="Test",
            message="Old Notification",
            created_at=timezone.now() - timezone.timedelta(minutes=1)
        )
        new_notification = Notification.objects.create(
            user=self.user1,
            notification_type="Test",
            message="New Notification",
            created_at=timezone.now()
        )
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertEqual(response.data['results'][0]['id'], new_notification.id)
        self.assertEqual(response.data['results'][0]['message'], "New Notification")
        self.assertEqual(response.data['results'][1]['id'], old_notification.id)
        self.assertEqual(response.data['results'][1]['message'], "Old Notification")

    def test_mark_all_notifications_as_read(self):
        """Test mark all notifications as read"""
        for i in range(5):
            Notification.objects.create(user=self.user1, notification_type="Test", message=f"Test Notification {i}")
        url = reverse("mark-all-notifications-read")
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unread_count = Notification.objects.filter(user=self.user1, is_read=False).count()
        self.assertEqual(unread_count, 0)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_celery_task_execution(self):
        """Test celery task execution"""
        post = Post.objects.create(author=self.user2, title="Test Post", content="Test Content")
        with patch('notifications.tasks.send_notification_task.delay') as mock_task:
            Comment.objects.create(post=post, author=self.user1, content="Test Comment")
            mock_task.assert_called_once_with(
                user_id=self.user2.id,
                notification_type="Comment",
                message=f"{self.user1.profile_name} commented on your post '{post.title}'."
            )

    def test_notification_for_non_existent_user(self):
        """Test notification for non-existent user"""
        with self.assertRaises(User.DoesNotExist):
            Notification.objects.create(user_id=9999, notification_type="Test", message="This should fail")

    def test_delete_notification(self):
        """Test delete notification"""
        notification = Notification.objects.create(user=self.user1, notification_type="Test", message="Test Notification")
        url = reverse("delete-notification", kwargs={"pk": notification.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_delete_other_user_notification(self):
        """Test delete other user's notification"""
        notification = Notification.objects.create(user=self.user2, notification_type="Test", message="Test Notification")
        url = reverse("delete-notification", kwargs={"pk": notification.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Notification.objects.filter(pk=notification.pk).exists())
