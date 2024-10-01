from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Follow

User = get_user_model()


class FollowTests(APITestCase):
    """Test suite for the Follow and Unfollow functionality."""

    def setUp(self):
        """Set up test users and URL for follow/unfollow actions."""
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

        self.follow_unfollow_url = reverse('follow-unfollow')

    def test_follow_user(self):
        """Test following another user."""
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.other_user.id}
        response = self.client.post(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.first().follower, self.user)

    def test_follow_yourself(self):
        """Test that a user cannot follow themselves."""
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.user.id}  
        response = self.client.post(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot follow yourself', str(response.data['error']))

    def test_follow_same_user_again(self):
        """Test that a user cannot follow the same user again."""
        self.client.force_authenticate(user=self.user)
        Follow.objects.create(follower=self.user, followed=self.other_user)
        data = {'followed': self.other_user.id}
        response = self.client.post(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are already following this user', str(response.data['error']))

    def test_unfollow_user(self):
        """Test unfollowing a user."""
        self.client.force_authenticate(user=self.user)
        Follow.objects.create(follower=self.user, followed=self.other_user)
        data = {'followed': self.other_user.id}
        response = self.client.delete(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Follow.objects.count(), 0)

    def test_unfollow_user_not_following(self):
        """Test that a user cannot unfollow a user they are not following."""
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.other_user.id}
        response = self.client.delete(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are not following this user', str(response.data['error']))

    def test_unfollow_yourself(self):
        """Test that a user cannot unfollow themselves."""
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.user.id}  
        response = self.client.delete(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are not following this user', str(response.data['error']))
        
    def test_follow_unfollow_updates_profile(self): 
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.other_user.id}
        response = self.client.post(reverse('follow-unfollow'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.other_user.profile.refresh_from_db()
        self.assertEqual(self.other_user.profile.follower_count, 1)
        response = self.client.delete(reverse('follow-unfollow'), data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.other_user.profile.refresh_from_db()
        self.assertEqual(self.other_user.profile.follower_count, 0)