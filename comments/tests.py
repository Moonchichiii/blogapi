from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Comment
from posts.models import Post
from .messages import STANDARD_MESSAGES


User = get_user_model()


class CommentTests(APITestCase):
    """Test suite for the Comment API."""

    def setUp(self):
        """Set up test data for each test."""
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
        self.comment_url = reverse('comment-list', kwargs={'post_id': self.post.id})

    def test_list_comments_as_unauthenticated_user(self):
        """Test that unauthenticated users cannot list comments."""
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['AUTHENTICATION_REQUIRED']['message'])

    def test_list_comments_as_authenticated_user(self):
        """Test that authenticated users can list comments."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['COMMENTS_RETRIEVED_SUCCESS']['message'])
