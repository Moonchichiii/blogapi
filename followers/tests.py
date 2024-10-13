from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profiles.models import Profile
from posts.models import Post
from .models import Follow

User = get_user_model()


class FollowTests(APITestCase):
    """Test suite for follow/unfollow functionality."""

    def setUp(self):
        """Set up the users and URL for follow/unfollow actions."""
        self.user = User.objects.create_user(
            email='testuser@example.com', profile_name='testuser', password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='otheruser@example.com', profile_name='otheruser', password='otherpass123'
        )
        self.follow_unfollow_url = reverse('follow-unfollow')

    def test_follow_user(self):
        """Test following another user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.follow_unfollow_url, {'followed': self.other_user.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.first().followed, self.other_user)

        response_data = response.data
        self.assertIn('data', response_data)
        self.assertEqual(response_data['message'], 'You have successfully followed the user.')
        self.assertEqual(response_data['type'], 'success')

    def test_unfollow_user(self):
        """Test unfollowing a user that is currently being followed."""
        Follow.objects.create(follower=self.user, followed=self.other_user)
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.other_user.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Follow.objects.count(), 0)

        response_data = response.data
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'You have successfully unfollowed the user.')
        self.assertEqual(response_data['type'], 'success')

    def test_follow_yourself(self):
        """Test that a user cannot follow themselves."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot follow yourself', str(response.data['error']))

    def test_follow_same_user_again(self):
        """Test that a user cannot follow the same user twice."""
        Follow.objects.create(follower=self.user, followed=self.other_user)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.follow_unfollow_url, {'followed': self.other_user.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are already following this user', str(response.data['error']))

    def test_unfollow_user_not_followed(self):
        """Test that a user cannot unfollow someone they are not following."""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.follow_unfollow_url, {'followed': self.other_user.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are not following this user', str(response.data['error']))


class PopularFollowersViewTests(APITestCase):
    """Test suite for popular followers view."""

    def setUp(self):
        """Set up users, posts, and follows for testing the popular followers."""
        self.user = User.objects.create_user(
            email='testuser@example.com', profile_name='testuser', password='testpass123'
        )
        self.follower1 = User.objects.create_user(
            email='follower1@example.com', profile_name='follower1', password='pass123'
        )
        self.follower2 = User.objects.create_user(
            email='follower2@example.com', profile_name='follower2', password='pass123'
        )

        # Create posts and ratings to calculate the popularity score
        Post.objects.create(author=self.follower1, title="Post 1", content="Content 1", average_rating=4.5)
        Post.objects.create(author=self.follower2, title="Post 2", content="Content 2", average_rating=3.0)

        # Create follows
        Follow.objects.create(follower=self.follower1, followed=self.user)
        Follow.objects.create(follower=self.follower2, followed=self.user)

        # Refresh profiles to calculate and save popularity scores
        self.follower1.profile.update_popularity_score()
        self.follower2.profile.update_popularity_score()

        self.popular_followers_url = reverse('popular-followers', kwargs={'user_id': self.user.id})

    def test_get_popular_followers(self):
        """Test retrieving popular followers ordered by their profile's popularity score."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.popular_followers_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        # Ensure that the most popular follower comes first (follower1 has higher popularity score)
        self.assertEqual(results[0]['profile_name'], 'follower1')
        self.assertEqual(results[1]['profile_name'], 'follower2')

        # Check that the popularity score is returned correctly
        self.assertGreater(results[0]['popularity_score'], results[1]['popularity_score'])

        # Verify post counts and average ratings are correct
        self.assertEqual(results[0]['post_count'], 1)
        self.assertEqual(results[0]['average_rating'], 4.5)
        self.assertEqual(results[1]['post_count'], 1)
        self.assertEqual(results[1]['average_rating'], 3.0)
