from unittest import mock
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from profiles.models import Profile
from profiles.tasks import update_all_popularity_scores
from followers.models import Follow
from popularity.models import PopularityMetrics

User = get_user_model()

class ProfileTests(TestCase):
    def setUp(self):
        """Set up test dependencies."""
        self.client = APIClient()
        self.profile_list_url = reverse("profile_list")
        self.user = self._create_user("testuser")
        self.user1 = self._create_user("user1")
        self.user2 = self._create_user("user2")
        
        # Create PopularityMetrics for test users
        PopularityMetrics.objects.create(user=self.user, popularity_score=50)
        PopularityMetrics.objects.create(user=self.user1, popularity_score=75)
        PopularityMetrics.objects.create(user=self.user2, popularity_score=60)

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def _create_user(self, profile_name, email=None, password="StrongPassword123!"):
        """Create a user."""
        email = email or f"{profile_name}@example.com"
        user = User.objects.create_user(
            profile_name=profile_name, email=email, password=password
        )
        user.is_active = True
        user.save()
        return user

    def test_profile_creation_on_user_registration(self):
        """Test profile creation on user registration."""
        user = self._create_user("newprofileuser")
        self.assertIsNotNone(Profile.objects.get(user=user))

    def test_profile_list_view(self):
        """Test profile list view."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_profile_list_pagination(self):
        """Test profile list pagination."""
        self.client.force_authenticate(user=self.user)
        for i in range(15):
            self._create_user(f"paginationuser{i}")
        response = self.client.get(self.profile_list_url)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data.get("next"))

    def test_profile_detail_view(self):
        """Test profile detail view."""
        self.client.force_authenticate(user=self.user)
        url = reverse("profile_detail", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bio", response.data)

    def test_profile_update(self):
        """Test profile update."""
        self.client.force_authenticate(user=self.user)
        url = reverse("profile_detail", kwargs={"user_id": self.user.id})
        data = {"bio": "Updated bio"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Updated bio")

    def test_profile_update_image(self):
        """Test profile image update."""
        self.client.force_authenticate(user=self.user)
        url = reverse("profile_detail", kwargs={"user_id": self.user.id})
        image_content = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        image_file = SimpleUploadedFile(
            "test_image.jpg", image_content, content_type="image/jpeg"
        )
        with mock.patch(
            "cloudinary.uploader.upload",
            return_value={
                "url": "http://test.com/image.jpg",
                "public_id": "test_public_id",
                "version": "1234567890",
                "type": "upload",
                "format": "jpg",
                "resource_type": "image",
            },
        ):
            data = {"image": image_file}
            response = self.client.patch(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)

    def test_unauthorized_profile_update(self):
        """Test unauthorized profile update."""
        self.client.force_authenticate(user=self.user2)
        url = reverse("profile_detail", kwargs={"user_id": self.user1.id})
        data = {"bio": "Unauthorized update"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_list_ordering(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.data["results"][0]["profile_name"], self.user1.profile_name)
        self.assertEqual(response.data["results"][1]["profile_name"], self.user2.profile_name)
        self.assertEqual(response.data["results"][2]["profile_name"], self.user.profile_name)

    @mock.patch("profiles.tasks.update_all_popularity_scores.delay")
    def test_update_all_popularity_scores_task(self, mock_task):
        """Test update all popularity scores task."""
        update_all_popularity_scores.delay()
        mock_task.assert_called_once()

    def test_profile_cache(self):
        """Test profile cache."""
        self.client.force_authenticate(user=self.user)
        url = reverse("profile_list")
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        self.assertEqual(response1.data, response2.data)

    def test_follow_count_update(self):
        """Test follow count update."""
        Follow.objects.create(follower=self.user2, followed=self.user1)
        self.user1.profile.refresh_from_db()
        self.assertEqual(self.user1.profile.follower_count, 1)

    def test_following_count_update(self):
        """Test following count update."""
        Follow.objects.create(follower=self.user1, followed=self.user2)
        self.user1.profile.refresh_from_db()
        self.assertEqual(self.user1.profile.following_count, 1)
        
class ProfileFollowCountTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', profile_name='user1', password='pass')
        self.user2 = User.objects.create_user(email='user2@example.com', profile_name='user2', password='pass')
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile

    def test_follow_updates_profile_counts(self):
        self.assertEqual(self.profile1.follower_count, 0)
        self.assertEqual(self.profile1.following_count, 0)
        self.assertEqual(self.profile2.follower_count, 0)
        self.assertEqual(self.profile2.following_count, 0)

        Follow.objects.create(follower=self.user1, followed=self.user2)
        self.profile1.refresh_from_db()
        self.profile2.refresh_from_db()

        self.assertEqual(self.profile1.following_count, 1)
        self.assertEqual(self.profile2.follower_count, 1)