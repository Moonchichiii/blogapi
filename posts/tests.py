from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from rest_framework import serializers

from comments.models import Comment
from ratings.models import Rating
from posts.models import Post
from posts.serializers import PostListSerializer, PostSerializer
from ratings.tasks import update_post_stats

from .tasks import send_email_task
from .messages import STANDARD_MESSAGES

User = get_user_model()

class PostTests(APITestCase):
    """Tests for Post model and views."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cache.clear()
        cls.client = APIClient()
        cls.user = cls._create_user("testuser@example.com", "testuser", "testpass123")
        cls.other_user = cls._create_user("otheruser@example.com", "otheruser", "otherpass123")
        cls.staff_user = cls._create_user("staffuser@example.com", "staffuser", "staffpass123", is_staff=True)
        cls.admin_user = cls._create_user("adminuser@example.com", "adminuser", "adminpass123", is_staff=True, is_superuser=True)

        now = timezone.now()
        cls.post1 = cls._create_post(cls.user, "First Post", "Content for the first post.", True, now - timedelta(minutes=2))
        cls.post2 = cls._create_post(cls.user, "Second Post", "Content for the second post.", False, now - timedelta(minutes=1))

        cls.post_list_url = reverse("post-list")
        cls.post_detail_url = lambda pk: reverse("post-detail", kwargs={"pk": pk})

    @staticmethod
    def _create_user(email, profile_name, password, is_staff=False, is_superuser=False):
        """Create a user."""
        return User.objects.create_user(email=email, profile_name=profile_name, password=password, is_staff=is_staff, is_superuser=is_superuser)

    @staticmethod
    def _create_post(author, title, content, is_approved=False, created_at=None):
        """Create a post."""
        post = Post.objects.create(author=author, title=title, content=content, is_approved=is_approved)
        if created_at:
            post.created_at = created_at
            post.save()
        return post

    def _authenticate_user(self, user):
        """Authenticate a user."""
        self.client.force_authenticate(user=user)

    def _assert_email_sent(self, subject, body_contains):
        """Assert an email was sent."""
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(body_contains, mail.outbox[0].body)

    def test_post_list(self):
        """Retrieve list of posts."""
        response = self.client.get(self.post_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_post_detail(self):
        """Retrieve post detail."""
        response = self.client.get(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], self.post1.title)

    def test_retrieve_nonexistent_post(self):
        """Retrieve nonexistent post."""
        response = self.client.get(self.post_detail_url(999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_unauthorized(self):
        """Update post without ownership."""
        self._authenticate_user(self.other_user)
        data = {"content": "Updated by non-owner"}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_post(self):
        """Create new post."""
        self._authenticate_user(self.user)
        data = {'title': 'New Post', 'content': 'New content', 'tags': [self.other_user.profile_name]}
        response = self.client.post(self.post_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.last().author, self.user)

    def test_update_post(self):
        """Update post."""
        self._authenticate_user(self.user)
        data = {'content': 'Updated content'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.content, 'Updated content')

    def test_delete_post(self):
        """Delete post."""
        self._authenticate_user(self.user)
        response = self.client.delete(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

    def test_approve_post(self):
        """Approve post."""
        self._authenticate_user(self.admin_user)
        response = self.client.patch(reverse('approve-post', kwargs={'pk': self.post2.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)

    def test_disapprove_post(self):
        """Disapprove post."""
        self._authenticate_user(self.admin_user)
        response = self.client.post(reverse('disapprove-post', kwargs={'pk': self.post1.id}), {'reason': 'Test reason'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)

    def test_unapproved_post_list(self):
        """Retrieve unapproved posts."""
        self._authenticate_user(self.admin_user)
        response = self.client.get(reverse('unapproved-posts'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    @patch("ratings.tasks.update_post_stats.delay")
    def test_post_rating_triggers_update_task(self, mock_update_task):
        """Rating triggers update task."""
        self._authenticate_user(self.other_user)
        response = self.client.post(reverse("create-update-rating"), {"post": self.post1.id, "value": 4})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_update_task.assert_called_once_with(self.post1.id)

    def test_post_search(self):
        """Search posts."""
        response = self.client.get(f"{self.post_list_url}?search=first")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "First Post")

    def test_post_ordering(self):
        """Order posts."""
        response = self.client.get(f"{self.post_list_url}?ordering=-created_at")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], "First Post")

    def test_post_filtering(self):
        """Filter posts."""
        self._authenticate_user(self.user)
        response = self.client.get(f"{self.post_list_url}?is_approved=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_post_with_image(self):
        """Create post with image."""
        self._authenticate_user(self.user)
        image_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        image_file = SimpleUploadedFile("test_image.gif", image_content, content_type="image/gif")
        data = {
            'title': 'Post with Image',
            'content': 'This post has an image.',
            'image': image_file,
            'tags': []
        }
        response = self.client.post(self.post_list_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Post.objects.get(title='Post with Image').image)

    def test_post_serializer(self):
        """Test Post serializer."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user
        context = {'request': request}
        serializer = PostSerializer(self.post1, context=context)
        expected_keys = {"id", "title", "content", "author", "created_at", "image", "is_owner", "average_rating", "tagged_users"}
        self.assertEqual(set(serializer.data.keys()), expected_keys)
        for key in expected_keys:
            self.assertIn(key, serializer.data)

    def test_post_list_serializer(self):
        """Test PostList serializer."""
        serializer = PostListSerializer(self.post1)
        self.assertEqual(set(serializer.data.keys()), {"id", "title", "content", "author", "created_at", "is_owner", "image"})

    @patch("posts.models.Post.objects.get")
    def test_update_post_stats_error(self, mock_get):
        """Handle update_post_stats errors."""
        mock_get.side_effect = Post.DoesNotExist
        update_post_stats(999)

    def test_validate_title_unique(self):
        serializer = PostSerializer()
        Post.objects.create(title="Existing Title", content="Content", author=self.user)
        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate_title("Existing Title")
            self.assertEqual(str(context.exception.detail[0]), 'A post with this title already exists.')

    def test_handle_tags(self):
        """Handle tags."""
        serializer = PostSerializer()
        post = Post.objects.create(title="Test Post", content="Content", author=self.user)
        tags_data = ["user1", "user2"]
        User.objects.create(email="user1@example.com", profile_name="user1")
        User.objects.create(email="user2@example.com", profile_name="user2")
        serializer._handle_tags(post, tags_data)
        assert post.tags.count() == 2
        assert set(post.tags.values_list('tagged_user__profile_name', flat=True)) == set(tags_data)

    def test_handle_tags_invalid_user(self):
        """Handle invalid user tags."""
        serializer = PostSerializer()
        post = Post.objects.create(title="Test Post", content="Content", author=self.user)
        tags_data = ["nonexistent_user"]
        with self.assertRaises(serializers.ValidationError):
            serializer._handle_tags(post, tags_data)

    @classmethod
    def explain_query(cls):
        """Explain SQL query."""
        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN {Post.objects.all().query}")
            for row in cursor.fetchall():
                print(row)

    def test_post_serializer_invalid_tags(self):
        """Invalid tag raises validation error."""
        self._authenticate_user(self.user)
        data = {"title": "Test Post", "content": "Test Content", "tags": ["invalid_user"]}
        serializer = PostSerializer(data=data, context={"request": self.client})
        self.assertFalse(serializer.is_valid())
        self.assertIn("tags", serializer.errors)

    def test_post_serializer_invalid_image(self):
        """Invalid image raises validation error."""
        self._authenticate_user(self.user)
        invalid_image_file = SimpleUploadedFile("test.txt", b"Invalid content", content_type="text/plain")
        data = {
            "title": "Post with invalid image",
            "content": "This post has an invalid image.",
            "image": invalid_image_file
        }
        response = self.client.post(self.post_list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)

    def test_post_list_pagination(self):
        """Test pagination."""
        self._authenticate_user(self.user)
        for i in range(15):
            self._create_post(self.user, f"Post {i+3}", "More content")
        response = self.client.get(f"{self.post_list_url}?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    @patch('django.core.cache.cache.set')
    @patch('django.core.cache.cache.get')
    @patch('rest_framework.throttling.UserRateThrottle.allow_request')
    def test_post_list_cache(self, mock_throttle, mock_cache_get, mock_cache_set):
        """Test post list caching."""
        mock_throttle.return_value = True  
        mock_cache_get.return_value = None
        response = self.client.get(self.post_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_cache_set.called)
        self.assertGreaterEqual(mock_cache_set.call_count, 1)

    def test_update_rating_statistics(self):
        """Update post rating statistics."""
        post = self._create_post(self.user, "Post to Rate", "Content", is_approved=True)
        self._authenticate_user(self.other_user)
        Rating.objects.create(user=self.other_user, post=post, value=4)
        Rating.objects.create(user=self.user, post=post, value=5)
        post.update_rating_statistics()
        post.refresh_from_db()
        self.assertEqual(post.average_rating, 4.5)
        self.assertEqual(post.total_ratings, 2)

    def test_post_is_approved_default(self):
        """New post is not approved by default."""
        post = self._create_post(self.user, "Unapproved Post", "Not approved yet")
        self.assertFalse(post.is_approved)

    @classmethod
    def tearDownClass(cls):
        """Clear cache after tests."""
        cache.clear()
        super().tearDownClass()

class SignalTests(TestCase):
    """Test signals on post save."""

    @patch('popularity.tasks.aggregate_popularity_score.delay')
    def test_post_save_triggers_signal(self, mock_aggregate_task):
        """Saving Post triggers popularity score update."""
        user = User.objects.create_user(email="user@example.com", profile_name="user", password="testpass")
        post = Post.objects.create(author=user, title="Test Post", content="Test Content")
        post.save()
        mock_aggregate_task.assert_called_once_with(post.author.id)

class TaskTests(TestCase):
    """Test Celery tasks."""

    def test_send_email_task(self):
        """Test send_email_task."""
        send_email_task("Test Subject", "Test Message", ["recipient@example.com"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        self.assertEqual(mail.outbox[0].body, "Test Message")
        self.assertIn("recipient@example.com", mail.outbox[0].to)
