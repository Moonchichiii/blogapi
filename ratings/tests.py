from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from posts.models import Post
from .models import Rating
from unittest.mock import patch, Mock
from ratings.tasks import update_post_stats

User = get_user_model()

class RatingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="testuser@example.com", profile_name="testuser", password="testpass123")
        cls.other_user = User.objects.create_user(email="otheruser@example.com", profile_name="otheruser", password="testpass123")
        cls.approved_post = Post.objects.create(author=cls.other_user, title="Approved Post", content="This is an approved post", is_approved=True)
        cls.unapproved_post = Post.objects.create(author=cls.other_user, title="Unapproved Post", content="This is an unapproved post", is_approved=False)
        cls.rating_url = reverse("create-update-rating")

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        Rating.objects.all().delete()

    def test_create_rating(self):
        """Test creating a rating for an approved post."""
        data = {"post": self.approved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(response.data["message"], "Rating created successfully.")

    def test_update_rating(self):
        """Test updating an existing rating."""
        Rating.objects.create(user=self.user, post=self.approved_post, value=3)
        data = {"post": self.approved_post.id, "value": 5}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 5)
        self.assertEqual(response.data["message"], "Rating updated successfully.")

    def test_rate_unapproved_post(self):
        """Test rating an unapproved post."""
        data = {"post": self.unapproved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["post"][0], "You cannot rate an unapproved post.")

    def test_invalid_rating_value(self):
        """Test rating with invalid values."""
        data = {"post": self.approved_post.id, "value": 6}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["value"][0], "Rating value must be between 1 and 5.")

        data = {"post": self.approved_post.id, "value": 0}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["value"][0], "Rating value must be between 1 and 5.")

    def test_rate_nonexistent_post(self):
        """Test rating a nonexistent post."""
        data = {"post": 9999, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not exist", str(response.data["post"][0]))

    def test_unauthenticated_user_cannot_rate(self):
        """Test unauthenticated user cannot rate."""
        self.client.force_authenticate(user=None)
        data = {"post": self.approved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_author_cannot_rate_own_post(self):
        """Test author cannot rate their own post."""
        self.client.force_authenticate(user=self.other_user)
        data = {"post": self.approved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0], "You cannot rate your own post.")

    @patch('ratings.tasks.Post.objects.get')
    @patch('ratings.tasks.aggregate_popularity_score.delay')
    def test_update_post_stats_success(self, mock_aggregate_task, mock_get_post):
        """Test successful update of post stats."""
        # Setup mock objects
        mock_post = Mock()
        mock_post.average_rating = 4.5
        mock_get_post.return_value = mock_post
    
        # Call the Celery task
        result = update_post_stats(1)
    
        # Assert that the correct result is returned
        self.assertIn("Updated stats for post 1", result)
    
        # Assert that the Celery task was called once
        mock_aggregate_task.assert_called_once_with(mock_post.author.id)


    @patch('ratings.tasks.Post.objects.get')
    def test_update_post_stats_general_exception(self, mock_get_post):
        """Test handling general exception during post stats update."""
        mock_get_post.side_effect = Exception("Test exception")
        result = update_post_stats(1)
        self.assertIn("Error updating stats for post 1", result)

    @patch('ratings.tasks.logger.info')
    @patch('ratings.tasks.Post.objects.get')
    def test_update_post_stats_logging(self, mock_get_post, mock_logger):
        """Test logging during post stats update."""
        mock_post = Mock()
        mock_post.average_rating = 4.5
        mock_get_post.return_value = mock_post
        update_post_stats(1)
        mock_logger.assert_any_call("Task None: Starting update_post_stats for post 1")
        mock_logger.assert_any_call("Task None: Updated rating statistics")