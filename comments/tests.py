from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment
from .messages import STANDARD_MESSAGES
from posts.models import Post

User = get_user_model()


class CommentTests(APITestCase):
    """Test suite for the Comment API."""

    def setUp(self):
        """Set up test data for each test."""
        self.user = User.objects.create_user(
            email="testuser@example.com",
            profile_name="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            email="otheruser@example.com",
            profile_name="otheruser",
            password="otherpass123",
        )
        self.post = Post.objects.create(
            author=self.user,
            title="Test Post",
            content="Test post content",
            is_approved=True,
        )
        self.comment1 = Comment.objects.create(
            post=self.post, author=self.user, content="First comment"
        )
        self.comment2 = Comment.objects.create(
            post=self.post, author=self.user, content="Second comment"
        )
        self.comment3 = Comment.objects.create(
            post=self.post, author=self.user, content="Third comment"
        )
        self.comment_url = reverse("comment-list", kwargs={"post_id": self.post.id})

    def test_list_comments_as_unauthenticated_user(self):
        """Test that unauthenticated users cannot list comments."""
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_list_comments_as_authenticated_user(self):
        """Test that authenticated users can list comments with pagination."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.count(), 3)

        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 3)
        else:
            self.fail("Pagination 'results' key not found in response")

        self.assertEqual(
            response.data["message"],
            STANDARD_MESSAGES["COMMENTS_RETRIEVED_SUCCESS"]["message"],
        )
        self.assertEqual(
            response.data["type"],
            STANDARD_MESSAGES["COMMENTS_RETRIEVED_SUCCESS"]["type"],
        )

    def test_create_comment_as_authenticated_user(self):
        """Test that authenticated users can create comments."""
        self.client.force_authenticate(user=self.user)
        data = {"content": "New comment"}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 4)
        self.client.force_authenticate(user=None)

    def test_create_comment_as_unauthenticated_user(self):
        """Test that unauthenticated users cannot create comments."""
        data = {"content": "New comment"}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_comment_as_owner(self):
        """Test that the owner can update their comment."""
        self.client.force_authenticate(user=self.user)
        update_url = reverse("comment-detail", kwargs={"pk": self.comment1.id})
        data = {"content": "Updated comment"}
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment1.refresh_from_db()
        self.assertEqual(self.comment1.content, "Updated comment")
        self.client.force_authenticate(user=None)

    def test_update_comment_as_non_owner(self):
        """Test that non-owners cannot update the comment."""
        self.client.force_authenticate(user=self.other_user)
        update_url = reverse("comment-detail", kwargs={"pk": self.comment1.id})
        data = {"content": "Updated comment"}
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

    def test_delete_comment_as_owner(self):
        """Test that the owner can delete their comment."""
        self.client.force_authenticate(user=self.user)
        delete_url = reverse("comment-detail", kwargs={"pk": self.comment1.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 2)
        self.client.force_authenticate(user=None)

    def test_delete_comment_as_non_owner(self):
        """Test that non-owners cannot delete the comment."""
        self.client.force_authenticate(user=self.other_user)
        delete_url = reverse("comment-detail", kwargs={"pk": self.comment1.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)
