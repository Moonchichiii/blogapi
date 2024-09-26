from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Rating
from posts.models import Post

User = get_user_model()

class RatingTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
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

        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Test post content',
            is_approved=True
        )

        self.rating_url = reverse('create-update-rating')

    def test_create_rating(self):
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 4)
        self.client.force_authenticate(user=None)

    def test_create_rating_as_unauthenticated_user(self):
        data = {'post': self.post.id, 'value': 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_rating(self):
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 3}
        self.client.post(self.rating_url, data)
        updated_data = {'post': self.post.id, 'value': 5}
        response = self.client.post(self.rating_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.first().value, 5)
        self.client.force_authenticate(user=None)

    def test_create_rating_for_non_existent_post(self):
        self.client.force_authenticate(user=self.user)
        data = {'post': 999, 'value': 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Post not found')
        self.client.force_authenticate(user=None)

    def test_create_rating_below_min_value(self):
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 0}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(user=None)

    def test_create_rating_above_max_value(self):
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 6}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(user=None)

    def test_create_rating_for_another_user_post(self):
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post.id, 'value': 5}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rating = Rating.objects.filter(post=self.post, user=self.other_user).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.value, 5)
        self.client.force_authenticate(user=None)

    def test_duplicate_rating_same_user(self):
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 3}
        self.client.post(self.rating_url, data)
        duplicate_data = {'post': self.post.id, 'value': 4}
        response = self.client.post(self.rating_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 4)
        self.client.force_authenticate(user=None)
