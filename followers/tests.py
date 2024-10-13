from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Follow

User = get_user_model()

class FollowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', profile_name='testuser', password='testpass123')
        self.other_user = User.objects.create_user(email='otheruser@example.com', profile_name='otheruser', password='otherpass123')
        self.follow_unfollow_url = reverse('follow-unfollow')

    def test_follow_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.follow_unfollow_url, {'followed': self.other_user.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow_user(self):
        Follow.objects.create(follower=self.user, followed=self.other_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.follow_unfollow_url, {'followed': self.other_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_yourself(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.follow_unfollow_url, {'followed': self.user.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You cannot follow yourself', str(response.data))
