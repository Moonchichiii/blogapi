from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from posts.models import Post
from comments.models import Comment
from tags.models import ProfileTag

User = get_user_model()

class ProfileTagAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            profile_name="testuser",
            password="testpass123",
        )
        cls.other_user = User.objects.create_user(
            email="otheruser@example.com",
            profile_name="otheruser",
            password="otherpass123",
        )
        cls.post = Post.objects.create(
            title="Test Post", content="Test Content", author=cls.user
        )
        cls.comment = Comment.objects.create(
            content="Test Comment", post=cls.post, author=cls.user
        )
        cls.post_content_type = ContentType.objects.get_for_model(Post)
        cls.comment_content_type = ContentType.objects.get_for_model(Comment)
        cls.tag_url = reverse("create-profile-tag")

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.client.force_authenticate(user=None)

    def test_create_tag_for_post(self):
        """Test creating a tag for a post."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Tag created successfully")

    def test_create_tag_for_comment(self):
        """Test creating a tag for a comment."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.comment_content_type.id,
            "object_id": self.comment.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Tag created successfully")

    def test_tagging_yourself(self):
        """Test that users cannot tag themselves."""
        data = {
            "tagged_user": self.user.id,
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0], "You cannot tag yourself."
        )

    def test_create_tag_with_invalid_object_id(self):
        """Test creating a tag with an invalid object ID."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.post_content_type.id,
            "object_id": 9999,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_create_tag_with_missing_fields(self):
        """Test creating a tag with missing fields."""
        data = {"tagged_user": self.other_user.id}
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_tag(self):
        """Test creating a duplicate tag."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(
            response.data["non_field_errors"][0],
            "The fields tagged_user, content_type, object_id must make a unique set."
        )

    def test_unauthenticated_user_cannot_create_tag(self):
        """Test that unauthenticated users cannot create tags."""
        self.client.force_authenticate(user=None)
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tag_deleted_when_post_is_deleted(self):
        """Test that tags are deleted when the associated post is deleted."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.post.delete()

        tag_exists = ProfileTag.objects.filter(
            tagged_user=self.other_user,
            content_type=self.post_content_type,
            object_id=self.post.id,
        ).exists()
        self.assertFalse(tag_exists)

    def test_tag_deleted_when_comment_is_deleted(self):
        """Test that tags are deleted when the associated comment is deleted."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": self.comment_content_type.id,
            "object_id": self.comment.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.comment.delete()

        tag_exists = ProfileTag.objects.filter(
            tagged_user=self.other_user,
            content_type=self.comment_content_type,
            object_id=self.comment.id,
        ).exists()
        self.assertFalse(tag_exists)

    def test_create_tag_with_nonexistent_user(self):
        """Test creating a tag with a nonexistent user."""
        data = {
            "tagged_user": 9999,
            "content_type": self.post_content_type.id,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tagged_user", response.data)

    def test_create_tag_with_nonexistent_content_type(self):
        """Test creating a tag with a nonexistent content type."""
        data = {
            "tagged_user": self.other_user.id,
            "content_type": 9999,
            "object_id": self.post.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content_type", response.data)
class TagSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            profile_name="testuser",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="otheruser@example.com",
            profile_name="otheruser",
            password="testpass123"
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user
        )
        self.post_content_type = ContentType.objects.get_for_model(Post)
        
        
    @patch('notifications.tasks.send_notification_task.delay')
    def test_create_tag_notification_signal(self, mock_send_notification):
        tag = ProfileTag.objects.create(
        tagged_user=self.other_user,
        tagger=self.user,
        content_type=self.post_content_type,
        object_id=self.post.id
        )

       # Check if the notification task was called
        mock_send_notification.assert_called_once_with(
            user_id=self.other_user.id,
            notification_type="Tag",
            message=f'You were tagged in a Post by {self.user.profile_name}.'
            )