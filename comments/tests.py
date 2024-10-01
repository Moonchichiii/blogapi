from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Comment
from posts.models import Post

User = get_user_model()


class CommentTests(APITestCase):
    """Test suite for the Comment API."""

    def setUp(self):
        """Set up test data for each test."""
        User.objects.all().delete()
        Post.objects.all().delete()
        Comment.objects.all().delete()

        self.user = User.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='otheruser@example.com',
            profile_name='otheruser',
            password='otherpass123'
        )

        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Test post content',
            is_approved=True
        )

        self.comment1 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='First comment'
        )
        self.comment2 = Comment.objects.create(
            post=self.post,
            author=self.other_user,
            content='Second comment'
        )

        self.comment_url = reverse('comment-list', kwargs={'post_id': self.post.id})
        self.comment_detail_url = reverse('comment-detail', kwargs={'pk': self.comment1.id})

    def tearDown(self):
        """Clean up test data after each test."""
        Comment.objects.all().delete()
        Post.objects.all().delete()
        User.objects.all().delete()

    def test_list_comments_as_unauthenticated_user(self):
        """Test that unauthenticated users cannot list comments."""
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_comments_as_authenticated_user(self):
        """Test that authenticated users can list comments."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.client.force_authenticate(user=None)

    def test_create_comment(self):
        """Test that authenticated users can create comments."""
        self.client.force_authenticate(user=self.user)
        data = {'content': 'New comment content'}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 3)
        self.client.force_authenticate(user=None)

    def test_create_comment_as_unauthenticated_user(self):
        """Test that unauthenticated users cannot create comments."""
        data = {'content': 'This comment should not be created.'}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_comment(self):
        """Test that authenticated users can retrieve a comment."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'First comment')
        self.client.force_authenticate(user=None)

    def test_update_comment_by_owner(self):
        """Test that the owner of a comment can update it."""
        self.client.force_authenticate(user=self.user)
        data = {'content': 'Updated content'}
        response = self.client.patch(self.comment_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment1.refresh_from_db()
        self.assertEqual(self.comment1.content, 'Updated content')
        self.client.force_authenticate(user=None)

    def test_update_comment_by_non_owner(self):
        """Test that non-owners cannot update a comment."""
        self.client.force_authenticate(user=self.other_user)
        data = {'content': 'Attempted update by non-owner'}
        response = self.client.patch(self.comment_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

    def test_delete_comment_by_owner(self):
        """Test that the owner of a comment can delete it."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment1.id).exists())
        self.client.force_authenticate(user=None)

    def test_delete_comment_by_non_owner(self):
        """Test that non-owners cannot delete a comment."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

    def test_create_comment_with_invalid_data(self):
        """Test that comments with invalid data cannot be created."""
        self.client.force_authenticate(user=self.user)
        data = {'content': ''}
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(user=None)

    def test_create_comment_for_non_existent_post(self):
        """Test that comments cannot be created for non-existent posts."""
        self.client.force_authenticate(user=self.user)
        invalid_url = reverse('comment-list', kwargs={'post_id': 999})
        data = {'content': 'Trying to comment on a non-existent post'}
        response = self.client.post(invalid_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.client.force_authenticate(user=None)
        
    def test_comment_creation_post_association(self):
        self.client.force_authenticate(user=self.user)
        post = Post.objects.create(author=self.user, title="Test Post", content="Test content")
        data = {"content": "This is a test comment"}
        response = self.client.post(reverse('comment-list', kwargs={'post_id': post.id}), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post.comments.count(), 1)