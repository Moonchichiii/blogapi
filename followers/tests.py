from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Follow

User = get_user_model()

class FollowTests(APITestCase):
    def setUp(self):
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

    # Test 1: Follow another user
    def test_follow_user(self):
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.other_user.id}
        response = self.client.post(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.first().follower, self.user)

    # Test 2: Follow yourself (should fail)
    def test_follow_yourself(self):
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.user.id}  # Trying to follow self
        response = self.client.post(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot follow yourself', str(response.data['error']))

    # Test 3: Follow the same user again (should fail)
    def test_follow_same_user_again(self):
        self.client.force_authenticate(user=self.user)
        Follow.objects.create(follower=self.user, followed=self.other_user)
        data = {'followed': self.other_user.id}
        response = self.client.post(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are already following this user', str(response.data['error']))

    # Test 4: Unfollow a user
    def test_unfollow_user(self):
        self.client.force_authenticate(user=self.user)
        Follow.objects.create(follower=self.user, followed=self.other_user)
        data = {'followed': self.other_user.id}
        response = self.client.delete(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Follow.objects.count(), 0)

    # Test 5: Unfollow a user you're not following (should fail)
    def test_unfollow_user_not_following(self):
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.other_user.id}
        response = self.client.delete(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are not following this user', str(response.data['error']))

    # Test 6: Unfollow yourself (should fail)
    def test_unfollow_yourself(self):
        self.client.force_authenticate(user=self.user)
        data = {'followed': self.user.id}  # Trying to unfollow self (edge case)
        response = self.client.delete(self.follow_unfollow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You are not following this user', str(response.data['error']))