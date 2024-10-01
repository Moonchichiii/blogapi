from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from posts.models import Post
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from .models import ProfileTag

User = get_user_model()


class TagTests(APITestCase):
    """Test suite for the ProfileTag API."""

    def setUp(self):
        """Set up test data for the tests."""
        # Create users
        self.user = User.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='testpass123'
        )
        self.user.is_active = True
        self.user.save()

        self.other_user = User.objects.create_user(
            email='otheruser@example.com',
            profile_name='otheruser',
            password='otherpass123'
        )
        self.other_user.is_active = True
        self.other_user.save()

        # Create Post and Comment
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Test post content',
            is_approved=True
        )
        self.comment = Comment.objects.create(
            author=self.user,
            post=self.post,
            content="Test comment"
        )

        # Content types for Post and Comment
        self.post_content_type = ContentType.objects.get_for_model(Post)
        self.comment_content_type = ContentType.objects.get_for_model(Comment)

        # Tag URL
        self.tag_url = reverse('create-profile-tag')

    def test_create_tag_for_post(self):
        """Test creating a tag for a post as an authenticated user."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProfileTag.objects.count(), 1)
        self.assertEqual(ProfileTag.objects.first().tagged_user, self.other_user)
        self.client.force_authenticate(user=None)

    def test_create_tag_for_comment(self):
        """Test creating a tag for a comment as an authenticated user."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.comment_content_type.id,
            'object_id': self.comment.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProfileTag.objects.count(), 1)
        self.assertEqual(ProfileTag.objects.first().content_object, self.comment)
        self.client.force_authenticate(user=None)

    def test_tagging_yourself(self):
        """Test tagging yourself (Edge Case)."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.user.id,  # Tagging self
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot tag yourself.', str(response.data))
        self.client.force_authenticate(user=None)

    def test_create_tag_invalid_content_type(self):
        """Test creating a tag for an invalid content type."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': 999,  # Invalid content type
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid content type', str(response.data))
        self.client.force_authenticate(user=None)

    def test_create_tag_for_non_existent_object(self):
        """Test creating a tag for a non-existent object."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': 9999  # Non-existent post/comment
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid object', str(response.data))
        self.client.force_authenticate(user=None)

    def test_duplicate_tag_for_same_object(self):
        """Test creating a duplicate tag for the same user on the same object (Edge Case)."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        # First tag
        self.client.post(self.tag_url, data)
        # Attempt duplicate tag
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duplicate', str(response.data).lower())
        self.client.force_authenticate(user=None)

    def test_create_tag_as_unauthenticated_user(self):
        """Test creating a tag as an unauthenticated user."""
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
