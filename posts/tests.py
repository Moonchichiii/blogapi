from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from django.db import connection
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from comments.models import Comment
from posts.models import Post
from posts.tasks import update_post_stats
from posts.serializers import LimitedPostSerializer, PostListSerializer
from .messages import STANDARD_MESSAGES

User = get_user_model()


class PostTests(APITestCase):
    """Test suite for post-related functionalities."""

    @classmethod
    def setUpTestData(cls):
        """Set up initial data once for the entire test case."""
        cache.clear()
        cls.client = APIClient()

        cls.user = cls._create_user("testuser@example.com", "testuser", "testpass123")
        cls.other_user = cls._create_user(
            "otheruser@example.com", "otheruser", "otherpass123"
        )
        cls.staff_user = cls._create_user(
            "staffuser@example.com", "staffuser", "staffpass123", is_staff=True
        )
        cls.admin_user = cls._create_user(
            "adminuser@example.com",
            "adminuser",
            "adminpass123",
            is_staff=True,
            is_superuser=True,
        )

        now = timezone.now()
        cls.post1 = cls._create_post(
            cls.user,
            "First Post",
            "Content for the first post.",
            True,
            now - timedelta(minutes=2),
        )
        cls.post2 = cls._create_post(
            cls.user,
            "Second Post",
            "Content for the second post.",
            False,
            now - timedelta(minutes=1),
        )

        cls.post_list_url = reverse("post-list")
        cls.post_detail_url = lambda pk: reverse("post-detail", kwargs={"pk": pk})

    @staticmethod
    def _create_user(email, profile_name, password, is_staff=False, is_superuser=False):
        """Helper method to create a user."""
        return User.objects.create_user(
            email=email,
            profile_name=profile_name,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

    @staticmethod
    def _create_post(author, title, content, is_approved=False, created_at=None):
        """Helper method to create a post."""
        post = Post.objects.create(
            author=author, title=title, content=content, is_approved=is_approved
        )
        if created_at:
            post.created_at = created_at
            post.save()
        return post

    def _authenticate_user(self, user):
        """Helper method to authenticate a user."""
        self.client.force_authenticate(user=user)

    def _assert_email_sent(self, subject, body_contains):
        """Helper method to assert email content."""
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(body_contains, mail.outbox[0].body)

    @patch("posts.tasks.update_post_stats.delay")
    def test_post_rating_triggers_update_task(self, mock_update_task):
        self._authenticate_user(self.other_user)
        response = self.client.post(
            reverse("create-update-rating"), {"post": self.post1.id, "value": 4}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_update_task.assert_called_once_with(self.post1.id)

    def test_post_disapproval_sends_email(self):
        """Test that disapproving a post sends an email."""
        self._authenticate_user(self.staff_user)
        response = self.client.post(
            reverse("disapprove-post", kwargs={"pk": self.post1.id}),
            {"reason": "Inappropriate content"},
        )
        self._assert_email_sent(
            "Your post has been disapproved", "Inappropriate content"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_update_with_invalid_image(self):
        """Test updating a post with an invalid image."""
        self._authenticate_user(self.user)
        invalid_file = SimpleUploadedFile(
            "invalid.txt", b"not an image", content_type="text/plain"
        )
        response = self.client.patch(
            self.post_detail_url(self.post1.id),
            {"image": invalid_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Upload a valid image.", str(response.data["image"][0]))

    def test_post_search_case_insensitive(self):
        """Test case-insensitive search for posts."""
        self._create_post(
            self.user, "Case Insensitive Search Test", "Test content", True
        )
        response = self.client.get(f"{self.post_list_url}?search=CASE INSENSITIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0]["title"], "Case Insensitive Search Test"
        )

    def test_post_update_resets_approval(self):
        """Test that updating a post resets its approval status."""
        self._authenticate_user(self.user)
        response = self.client.patch(
            self.post_detail_url(self.post1.id), {"content": "Updated content"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)

    def test_post_creation_with_invalid_tags(self):
        """Test creating a post with invalid tags."""
        self._authenticate_user(self.user)
        response = self.client.post(
            self.post_list_url,
            {
                "title": "Post with Invalid Tags",
                "content": "Content with invalid tags",
                "tags": ["nonexistent_user", self.other_user.profile_name],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data["errors"])

    def test_post_detail_includes_comments(self):
        """Test that post detail includes comments."""
        self._authenticate_user(self.user)
        Comment.objects.create(
            post=self.post1, author=self.other_user, content="Test comment"
        )
        response = self.client.get(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["comments"]), 1)
        self.assertEqual(
            response.data["data"]["comments"][0]["content"], "Test comment"
        )

    def test_partial_update_post(self):
        """Test partially updating a post."""
        self._authenticate_user(self.user)
        data = {"content": "Partially updated content"}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.content, "Partially updated content")

    def test_create_post_with_tags_and_image(self):
        """Test creating a post with both tags and an image."""
        self.client.force_authenticate(user=self.user)
        image_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        image_file = SimpleUploadedFile(
            "test_image.gif", image_content, content_type="image/gif"
        )
        data = {
            "title": "Post with Tags and Image",
            "content": "This post has tags and an image.",
            "tags": [self.other_user.profile_name],
            "image": image_file,
        }
        response = self.client.post(self.post_list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title="Post with Tags and Image")
        self.assertIsNotNone(new_post.image)
        self.assertEqual(new_post.tags.count(), 1)

    def test_post_list_filter_by_approval_status(self):
        """Test filtering posts by approval status."""
        self._authenticate_user(self.user)
        response = self.client.get(f"{self.post_list_url}?is_approved=True")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_post_with_duplicate_title(self):
        self._authenticate_user(self.user)
        data = {
            "title": "First Post",
            "content": "Trying to create a post with a duplicate title.",
            "tags": [self.other_user.profile_name],
        }
        response = self.client.post(self.post_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "A post with this title already exists.",
            str(response.data["errors"]["title"][0]),
        )

    def test_create_post_unexpected_exception(self):
        self._authenticate_user(self.user)
        data = {
            "title": "New Post",
            "content": "Content for the new post.",
            "tags": [self.other_user.profile_name],
        }
        with patch(
            "posts.serializers.PostSerializer.is_valid",
            side_effect=Exception("Test exception"),
        ):
            response = self.client.post(self.post_list_url, data)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertIn("Test exception", response.data["errors"]["detail"])

        with patch(
            "posts.serializers.PostSerializer.is_valid",
            side_effect=Exception("Test exception"),
        ):
            response = self.client.post(self.post_list_url, data)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertIn("Test exception", response.data["errors"]["detail"])

    @patch("posts.models.Post.objects.get")
    def test_update_post_stats_error(self, mock_get):
        """Test error handling in update_post_stats task."""
        mock_get.side_effect = Post.DoesNotExist
        update_post_stats(999)

    @classmethod
    def explain_query(cls):
        """Helper method to print SQL EXPLAIN output."""
        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN {Post.objects.all().query}")
            for row in cursor.fetchall():
                print(row)

    def test_limited_post_serializer(self):
        """Test the LimitedPostSerializer."""
        serializer = LimitedPostSerializer(self.post1)
        data = serializer.data
        self.assertEqual(set(data.keys()), {"id", "title", "author", "image_url"})
        self.assertEqual(data["author"], self.user.profile_name)
