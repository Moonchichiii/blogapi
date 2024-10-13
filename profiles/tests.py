from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from followers.models import Follow
from posts.models import Post
from profiles.models import Profile
from profiles.serializers import PopularFollowerSerializer, ProfileSerializer
from profiles.tasks import update_all_popularity_scores
from ratings.models import Rating

User = get_user_model()


class ProfileTests(TestCase):
    """Test suite for Profile-related functionalities."""

    def setUp(self):
        """Set up test dependencies."""
        self.client = APIClient()
        self.update_profile_url = reverse("current_user_profile")
        self.profile_list_url = reverse("profile_list")
        self.user = self._create_user("testuser")
        self.user1 = self._create_user("user1")
        self.user2 = self._create_user("user2")
        self.post1 = Post.objects.create(
            author=self.user1, title="Test Post 1", content="Test content 1"
        )
        self.post2 = Post.objects.create(
            author=self.user2, title="Test Post 2", content="Test content 2"
        )

    def _create_user(self, profile_name, email=None, password="StrongPassword123!"):
        """Helper function to create a user."""
        if email is None:
            email = f"{profile_name}_{User.objects.count()}@example.com"
        profile_name = f"{profile_name}_{User.objects.count()}"
        user = User.objects.create_user(
            profile_name=profile_name, email=email, password=password
        )
        user.is_active = True
        user.save()
        return user

    def test_public_can_view_profile(self):
        """Test that public users can view profiles."""
        profile_view_url = reverse("profile_detail", kwargs={"user_id": self.user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bio", response.data)
        self.assertEqual(response.data.get("bio", ""), self.user.profile.bio)

    def test_authenticated_user_can_update_profile(self):
        """Test that authenticated users can update their profiles."""
        self.client.force_authenticate(user=self.user)
        data = {"bio": "Updated bio"}
        response = self.client.patch(self.update_profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Updated bio")

    def test_unauthorized_user_cannot_update_profile(self):
        """Test that unauthorized users cannot update other users' profiles."""
        self.client.force_authenticate(user=self.user2)
        update_url = reverse("profile_detail", kwargs={"user_id": self.user1.id})
        data = {"bio": "Unauthorized update"}
        response = self.client.patch(update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_creation_on_user_registration(self):
        """Test that a profile is created when a user registers."""
        user = self._create_user("newprofileuser")
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile)

    def test_popularity_score_updates_with_ratings(self):
        """Test that popularity score updates correctly with ratings."""
        Rating.objects.create(user=self.user2, post=self.post1, value=5)
        self.post1.update_rating_statistics()
        self.user1.profile.update_popularity_score()
        self.assertGreater(self.user1.profile.popularity_score, 0)

    def test_follower_count_updates_on_follow(self):
        """Test that follower count updates correctly when a user is followed."""
        Follow.objects.create(follower=self.user2, followed=self.user1)
        self.user1.profile.update_counts()
        self.assertEqual(self.user1.profile.follower_count, 1)

    def test_profile_list_is_paginated(self):
        """Test that profile list is paginated."""
        for i in range(15):
            self._create_user(f"user{i}")
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)

    def test_profile_update_with_invalid_data(self):
        """Test that invalid profile update returns error."""
        self.client.force_authenticate(user=self.user)
        data = {"bio": "a" * 501}
        response = self.client.patch(self.update_profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_list_ordering_by_popularity(self):
        """Test that profiles are ordered by popularity score."""
        self.user1.profile.popularity_score = 50
        self.user1.profile.save()
        self.user2.profile.popularity_score = 100
        self.user2.profile.save()
        response = self.client.get(self.profile_list_url)
        self.assertEqual(
            response.data["results"][0]["profile_name"],
            self.user2.profile.user.profile_name,
        )
        self.assertEqual(
            response.data["results"][1]["profile_name"],
            self.user1.profile.user.profile_name,
        )

    def test_profile_serializer_hides_email_for_non_owner(self):
        """Test that profile serializer hides the email for non-owners."""
        self.client.force_authenticate(user=self.user2)
        profile_view_url = reverse("profile_detail", kwargs={"user_id": self.user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("email", response.data)
        self.assertIn("bio", response.data)
        self.assertIn("tags", response.data)

    @patch("profiles.tasks.update_all_popularity_scores.delay")
    def test_update_all_popularity_scores_task(self, mock_task):
        """Test that popularity scores update task runs successfully."""
        update_all_popularity_scores.delay()
        mock_task.assert_called_once()
