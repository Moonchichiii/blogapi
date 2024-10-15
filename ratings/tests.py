from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from posts.models import Post
from .models import Rating

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

    def test_create_rating(self):
        data = {"post": self.approved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(response.data["message"], "Rating created successfully.")

    def test_update_rating(self):
        Rating.objects.create(user=self.user, post=self.approved_post, value=3)
        data = {"post": self.approved_post.id, "value": 5}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.count(), 1)
        self.assertEqual(Rating.objects.first().value, 5)
        self.assertEqual(response.data["message"], "Rating updated successfully.")

    def test_rate_unapproved_post(self):
        data = {"post": self.unapproved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["post"][0], "You cannot rate an unapproved post.")

    def test_invalid_rating_value(self):
        # Test value above maximum
        data = {"post": self.approved_post.id, "value": 6}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["value"][0], "Rating value must be between 1 and 5.")

        # Test value below minimum
        data = {"post": self.approved_post.id, "value": 0}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["value"][0], "Rating value must be between 1 and 5.")

    def test_rate_nonexistent_post(self):
        data = {"post": 9999, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not exist", str(response.data["post"][0]))

    def test_unauthenticated_user_cannot_rate(self):
        self.client.force_authenticate(user=None)
        data = {"post": self.approved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_author_cannot_rate_own_post(self):
        self.client.force_authenticate(user=self.other_user)
        data = {"post": self.approved_post.id, "value": 4}
        response = self.client.post(self.rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["non_field_errors"][0], "You cannot rate your own post.")