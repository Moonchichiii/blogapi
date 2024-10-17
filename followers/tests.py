from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.db import IntegrityError 
from .models import Follow
from profiles.models import Profile
from .serializers import FollowSerializer
User = get_user_model()

class FollowTests(APITestCase):
    """Test suite for Follow and Unfollow functionality."""

    def setUp(self):
        """Set up test users and URL for follow/unfollow actions."""
        self.user1 = User.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='testpass123'
        )
        self.user1.is_active = True
        self.user1.save()

        self.user2 = User.objects.create_user(
            email='otheruser@example.com',
            profile_name='otheruser',
            password='otherpass123'
        )
        self.user2.is_active = True
        self.user2.save()

        self.follow_unfollow_url = reverse('follow-unfollow')
        self.client.force_authenticate(user=self.user1)

    def test_follow_user_success(self):
        """Test successful follow action."""
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Follow.objects.filter(follower=self.user1, followed=self.user2).exists())
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.profile.follower_count, 1)

    def test_follow_self_fails(self):
        """Test that a user cannot follow themselves."""
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_duplicate_follow_fails(self):
        """Test that a user cannot follow someone they are already following."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_unfollow_user_success(self):
        """Test successful unfollow action."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follow.objects.filter(follower=self.user1, followed=self.user2).exists())
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.profile.follower_count, 0)

    def test_unfollow_user_not_following(self):
        """Test unfollowing a user who is not followed returns an error."""
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_invalid_followed_id(self):
        """Test that providing an invalid user ID for following fails."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.follow_unfollow_url, {'followed': 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "The user you're trying to follow doesn't exist.")

    def test_follower_count_updated_on_follow(self):
        """Test that the follower count increases upon a successful follow."""
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.profile.follower_count, 1)

    def test_follower_count_updated_on_unfollow(self):
        """Test that the follower count decreases upon a successful unfollow."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.profile.follower_count, 0)

    @patch('followers.signals.invalidate_follower_cache')
    def test_cache_invalidation_on_follow(self, mock_invalidate_follower_cache):
        """Test that the cache is invalidated when a user is followed."""
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_invalidate_follower_cache.assert_any_call(self.user2.id)
        mock_invalidate_follower_cache.assert_any_call(self.user1.id)

    @patch('followers.signals.invalidate_follower_cache')
    def test_cache_invalidation_on_unfollow(self, mock_invalidate_follower_cache):
        """Test that the cache is invalidated when a user is unfollowed."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_invalidate_follower_cache.assert_any_call(self.user2.id)
        mock_invalidate_follower_cache.assert_any_call(self.user1.id)

    def test_follow_unauthenticated_user(self):
        """Test that an unauthenticated user cannot follow someone."""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unfollow_unauthenticated_user(self):
        """Test that an unauthenticated user cannot unfollow someone."""
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.user2.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_no_followed_id(self):
        """Test that following without providing a followed ID fails."""
        response = self.client.post(self.follow_unfollow_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unfollow_no_followed_id(self):
        """Test that unfollowing without providing a followed ID fails."""
        response = self.client.delete(self.follow_unfollow_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        
class FollowModelTests(TestCase):
    """Test suite for the Follow model."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            profile_name='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            profile_name='user2',
            password='testpass123'
        )

    def test_follow_creation(self):
        """Test follow creation."""
        follow = Follow.objects.create(follower=self.user1, followed=self.user2)
        self.assertIsInstance(follow, Follow)
        self.assertEqual(str(follow), f"{self.user1.profile_name} follows {self.user2.profile_name}")

    def test_follow_unique_constraint(self):
        """Test unique constraint on follow."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.user1, followed=self.user2)

class FollowTaskTests(TestCase):
    """Test suite for follow tasks."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            profile_name='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            profile_name='user2',
            password='testpass123'
        )

    @patch('followers.tasks.Notification.objects.create')
    def test_send_notification_task(self, mock_create_notification):
        """Test send notification task."""
        from followers.tasks import send_notification_task
        
        send_notification_task(self.user1.id, 'follow', 'You have a new follower')
        mock_create_notification.assert_called_once_with(
            user_id=self.user1.id,
            notification_type='follow',
            message='You have a new follower'
        )

    def test_remove_follows_for_user(self):
        """Test remove follows for user."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        Follow.objects.create(follower=self.user2, followed=self.user1)
        
        from followers.tasks import remove_follows_for_user
        remove_follows_for_user(self.user1.id)
        
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_serializer_create(self):
        user3 = User.objects.create(email="user3@example.com", profile_name="user3")
        user4 = User.objects.create(email="user4@example.com", profile_name="user4")
    
        # Only include 'followed' in the initial data
        data = {'followed': user4.id}
    
        serializer = FollowSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
        # Simulate how the view would create a Follow instance
        follow = serializer.save(follower=user3)
    
        self.assertIsInstance(follow, Follow)
        self.assertEqual(follow.follower, user3)
        self.assertEqual(follow.followed, user4)
    
        # Verify that the create method was called with the correct data
        print("Serializer validated_data:", serializer.validated_data)
        print("Created Follow instance:", follow)

    def test_follow_serializer_update(self):
        user5 = User.objects.create(email="user5@example.com", profile_name="user5")
        user6 = User.objects.create(email="user6@example.com", profile_name="user6")
        user7 = User.objects.create(email="user7@example.com", profile_name="user7")
        follow = Follow.objects.create(follower=user5, followed=user6)
        serializer = FollowSerializer(follow, data={'followed': user7.id}, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_follow = serializer.update(follow, serializer.validated_data)
        self.assertEqual(updated_follow.followed, user7)