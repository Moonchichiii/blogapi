from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from comments.models import Comment
from posts.models import Post
from .messages import STANDARD_MESSAGES
from .models import ProfileTag

User = get_user_model()

class ProfileTagAPITests(APITestCase):
    """Test suite for the ProfileTag API."""

    def setUp(self):
        """Set up test data for the tests."""
        self._create_test_users()
        self._create_test_post_and_comment()
        self._set_content_types()
        self.tag_url = reverse('create-profile-tag')

    def _create_test_users(self):
        """Create test users."""
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

    def _create_test_post_and_comment(self):
        """Create a test post and comment."""
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

    def _set_content_types(self):
        """Set content types for post and comment."""
        self.post_content_type = ContentType.objects.get_for_model(Post)
        self.comment_content_type = ContentType.objects.get_for_model(Comment)

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
        """Test that a user cannot tag themselves."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.user.id,
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], STANDARD_MESSAGES['CANNOT_TAG_SELF']['message'])

    def test_create_tag_invalid_content_type(self):
        """Test creating a tag with an invalid content type."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': 999,
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], STANDARD_MESSAGES['INVALID_CONTENT_TYPE']['message'])

    def test_create_tag_for_non_existent_object(self):
        """Test creating a tag for a non-existent object."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': 9999
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Invalid object.")

    def test_duplicate_tag_for_same_object(self):
        """Test creating a duplicate tag for the same object."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        response_first = self.client.post(self.tag_url, data)
        self.assertEqual(response_first.status_code, status.HTTP_201_CREATED)

        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['errors']['non_field_errors'][0], "The fields tagged_user, content_type, object_id must make a unique set.")

    def test_create_tag_as_unauthenticated_user(self):
        """Test creating a tag as an unauthenticated user."""
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': self.post.id
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tag_with_invalid_object_id(self):
        """Test creating a tag with an invalid object ID."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
            'content_type': self.post_content_type.id,
            'object_id': 'invalid'
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Invalid content type for tagging.")
        self.client.force_authenticate(user=None)

    def test_create_tag_with_missing_fields(self):
        """Test creating a tag with missing fields."""
        self.client.force_authenticate(user=self.user)
        data = {
            'tagged_user': self.other_user.id,
        }
        response = self.client.post(self.tag_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(user=None)
