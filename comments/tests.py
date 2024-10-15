from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Comment
from posts.models import Post

User = get_user_model()

class CommentTests(APITestCase):
    def setUp(self):
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
            post=self.post, author=self.user, content="First comment", is_approved=True
        )
        self.comment2 = Comment.objects.create(
            post=self.post, author=self.user, content="Second comment", is_approved=True
        )
        self.comment3 = Comment.objects.create(
            post=self.post, author=self.user, content="Third comment", is_approved=True
        )
        self.comment_url = reverse("comment-list", kwargs={"post_id": self.post.id})

    def test_list_comments_as_unauthenticated_user(self):
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_comments_as_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_create_comment_as_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        data = {"content": "New comment"}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 4)
        self.assertEqual(response.data["content"], "New comment")
        self.assertEqual(response.data["post"], self.post.id)
        self.assertEqual(response.data["author"], self.user.profile_name)

    def test_create_comment_as_unauthenticated_user(self):
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
        self.assertEqual(response.data["content"], "Updated comment")
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

    def test_moderate_comment_as_admin(self):
        """Test that admin users can moderate comments."""
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            profile_name="admin",
            password="adminpass123",
        )
        self.client.force_authenticate(user=admin_user)
        moderate_url = reverse("comment-moderate", kwargs={"pk": self.comment1.id})
        
        # Test approving a comment
        response = self.client.patch(moderate_url, {"action": "approve"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "Comment approved successfully")
        
        # Test disapproving a comment
        response = self.client.patch(moderate_url, {"action": "disapprove"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "Comment disapproved successfully")
        
        self.client.force_authenticate(user=None)

    def test_moderate_comment_as_non_admin(self):
        """Test that non-admin users cannot moderate comments."""
        self.client.force_authenticate(user=self.user)
        moderate_url = reverse("comment-moderate", kwargs={"pk": self.comment1.id})
        response = self.client.patch(moderate_url, {"action": "approve"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)