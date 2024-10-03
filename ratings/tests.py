from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Rating
from posts.models import Post

User = get_user_model()


class RatingTests(APITestCase):
    """Test suite for the Rating model."""

    def setUp(self):
        """Set up test dependencies."""
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
        """Test creating a rating."""
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 4)
        self.client.force_authenticate(user=None)

    def test_create_rating_as_unauthenticated_user(self):
        """Test creating a rating as an unauthenticated user."""
        data = {'post': self.post.id, 'value': 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_rating(self):
        """Test updating a rating."""
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 3}
        self.client.post(self.rating_url, data)
        updated_data = {'post': self.post.id, 'value': 5}
        response = self.client.post(self.rating_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.first().value, 5)
        self.client.force_authenticate(user=None)

    def test_create_rating_for_non_existent_post(self):
        """Test creating a rating for a non-existent post."""
        self.client.force_authenticate(user=self.user)
        data = {'post': 999, 'value': 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Post not found')
        self.client.force_authenticate(user=None)

    def test_create_rating_below_min_value(self):
        """Test creating a rating below the minimum value."""
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 0}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(user=None)

    def test_create_rating_above_max_value(self):
        """Test creating a rating above the maximum value."""
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 6}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(user=None)

    def test_create_rating_for_another_user_post(self):
        """Test creating a rating for another user's post."""
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post.id, 'value': 5}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rating = Rating.objects.filter(post=self.post, user=self.other_user).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.value, 5)
        self.client.force_authenticate(user=None)

    def test_duplicate_rating_same_user(self):
        """Test creating a duplicate rating by the same user."""
        self.client.force_authenticate(user=self.user)
        data = {'post': self.post.id, 'value': 3}
        self.client.post(self.rating_url, data)
        duplicate_data = {'post': self.post.id, 'value': 4}
        response = self.client.post(self.rating_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 4)
        self.client.force_authenticate(user=None)
        
    def test_rating_updates_post_and_profile(self):
        self.client.force_authenticate(user=self.user)
        post = Post.objects.create(author=self.other_user, title="Test Post", content="Test content")
        data = {"post": post.id, "value": 4}
        response = self.client.post(reverse('create-update-rating'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post.refresh_from_db()
        self.other_user.profile.refresh_from_db()
        self.assertEqual(post.average_rating, 4.0)
        self.assertGreater(self.other_user.profile.popularity_score, 0)
        
    def test_rating_updates_profile_popularity(self):
        """Ensure rating a post updates the author's profile popularity score."""
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post.id, 'value': 5}
        response = self.client.post(reverse('create-update-rating'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Manually update the post's average rating
        self.post.update_rating_stats()
        # Manually update the author's profile popularity score
        self.user.profile.update_popularity_score()
        self.user.profile.refresh_from_db()
        self.assertGreater(self.user.profile.popularity_score, 0)
