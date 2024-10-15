from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.cache import cache
from followers.models import Follow
from posts.models import Post
from profiles.models import Profile

from popularity.models import PopularityMetrics

User = get_user_model()

class FollowTests(APITestCase):
    """Tests for follow/unfollow functionality."""

    def setUp(self):
        """Set up users and URL."""
        self.user = User.objects.create_user(
            email="testuser@example.com",
            profile_name="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            email="otheruser@example.com",
            profile_name="otheruser",
            password="otherpass123",
        )
        Profile.objects.get_or_create(user=self.user)
        Profile.objects.get_or_create(user=self.other_user)
        self.follow_unfollow_url = reverse("follow-unfollow")

    def test_follow_user(self):
        """Test following another user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.follow_unfollow_url, {"followed": self.other_user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.first().followed, self.other_user)
        response_data = response.data
        self.assertIn("data", response_data)
        self.assertEqual(
            response_data["message"], "You have successfully followed the user."
        )
        self.assertEqual(response_data["type"], "success")

    def test_unfollow_user(self):
        """Test unfollowing a user."""
        Follow.objects.create(follower=self.user, followed=self.other_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            self.follow_unfollow_url, {"followed": self.other_user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Follow.objects.count(), 0)
        response_data = response.data
        self.assertIn("message", response_data)
        self.assertEqual(
            response_data["message"], "You have successfully unfollowed the user."
        )
        self.assertEqual(response_data["type"], "success")

    def test_follow_yourself(self):
        """Test that a user cannot follow themselves."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.follow_unfollow_url, {"followed": self.user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You cannot follow yourself", str(response.data["error"]))

    def test_follow_same_user_again(self):
        """Test that a user cannot follow the same user twice."""
        Follow.objects.create(follower=self.user, followed=self.other_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.follow_unfollow_url, {"followed": self.other_user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "You are already following this user", str(response.data["error"])
        )

    def test_unfollow_user_not_followed(self):
        """Test that a user cannot unfollow someone they are not following."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            self.follow_unfollow_url, {"followed": self.other_user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You are not following this user", str(response.data["error"]))

class PopularFollowersViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", profile_name="testuser", password="testpass123"
        )
        self.follower1 = User.objects.create_user(
            email="follower1@example.com", profile_name="follower1", password="pass123"
        )
        self.follower2 = User.objects.create_user(
            email="follower2@example.com", profile_name="follower2", password="pass123"
        )

        self.profile = Profile.objects.get(user=self.user)
        self.follower1_profile = Profile.objects.get(user=self.follower1)
        self.follower2_profile = Profile.objects.get(user=self.follower2)

        Post.objects.create(
            author=self.follower1, title="Post 1", content="Content 1", average_rating=4.5
        )
        Post.objects.create(
            author=self.follower2, title="Post 2", content="Content 2", average_rating=3.0
        )

        Follow.objects.create(follower=self.follower1, followed=self.user)
        Follow.objects.create(follower=self.follower2, followed=self.user)

        PopularityMetrics.objects.create(user=self.user, popularity_score=50)
        PopularityMetrics.objects.create(user=self.follower1, popularity_score=75)
        PopularityMetrics.objects.create(user=self.follower2, popularity_score=60)

        self.popular_followers_url = reverse("popular-followers", kwargs={"user_id": self.user.id})

    def test_get_popular_followers(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.popular_followers_url}?order_by=popularity")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("data", [])
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["profile_name"], "follower1")
        self.assertEqual(results[1]["profile_name"], "follower2")
        self.assertGreater(results[0]["popularity_score"], results[1]["popularity_score"])


class FollowSignalTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", profile_name="user", password="pass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", profile_name="otheruser", password="pass123"
        )

        self.profile = Profile.objects.get(user=self.user)
        self.other_profile = Profile.objects.get(user=self.other_user)

        # Create PopularityMetrics for both users
        PopularityMetrics.objects.create(user=self.user, popularity_score=50)
        PopularityMetrics.objects.create(user=self.other_user, popularity_score=50)

        self.follow_unfollow_url = reverse("follow-unfollow")

    def test_follow_cache_invalidation(self):
        """Test that follow action invalidates the cache for both users."""
        cache.set(f"user_{self.user.id}_follower_list", "cached_data")
        cache.set(f"user_{self.other_user.id}_follower_list", "cached_data")

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.follow_unfollow_url, {"followed": self.other_user.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIsNone(cache.get(f"user_{self.user.id}_follower_list"))
        self.assertIsNone(cache.get(f"user_{self.other_user.id}_follower_list"))

    def test_unfollow_cache_invalidation(self):
        """Test that unfollow action invalidates the cache for both users."""
        Follow.objects.create(follower=self.user, followed=self.other_user)
        cache.set(f"user_{self.user.id}_follower_list", "cached_data")
        cache.set(f"user_{self.other_user.id}_follower_list", "cached_data")

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.follow_unfollow_url, {"followed": self.other_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(cache.get(f"user_{self.user.id}_follower_list"))
        self.assertIsNone(cache.get(f"user_{self.other_user.id}_follower_list"))

    def test_follow_updates_popularity_score(self):
        """Test that follow action updates the popularity score."""
        self.client.force_authenticate(user=self.user)
        self.client.post(self.follow_unfollow_url, {"followed": self.other_user.id})

        popularity_metrics = PopularityMetrics.objects.get(user=self.other_user)
        self.assertGreater(popularity_metrics.popularity_score, 0)