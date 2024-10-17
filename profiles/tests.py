import unittest
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from profiles.models import Profile
from followers.models import Follow
from popularity.models import PopularityMetrics
from .tasks import update_all_popularity_scores
from backend.utils import validate_image

User = get_user_model()

class ProfileListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(email='user1@example.com', profile_name='user1', password='pass')
        self.user2 = User.objects.create_user(email='user2@example.com', profile_name='user2', password='pass')
        self.user3 = User.objects.create_user(email='user3@example.com', profile_name='user3', password='pass')
        PopularityMetrics.objects.filter(user=self.user1).update(popularity_score=50)
        PopularityMetrics.objects.filter(user=self.user2).update(popularity_score=75)
        PopularityMetrics.objects.filter(user=self.user3).update(popularity_score=25)
        Follow.objects.create(follower=self.user1, followed=self.user2)
        self.profile_list_url = reverse('profile_list')

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()
        Follow.objects.all().delete()
        PopularityMetrics.objects.all().delete()

    def test_profile_list_popular_filter(self):
        """Test profile list ordered by popularity."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['profile_name'], 'user2')
        self.assertEqual(response.data['results'][1]['profile_name'], 'user1')
        self.assertEqual(response.data['results'][2]['profile_name'], 'user3')

    def test_profile_list_followed_filter(self):
        """Test profile list filtered by followed users."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{self.profile_list_url}?filter=followed")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['profile_name'], 'user2')

    def test_profile_list_pagination(self):
        """Test profile list pagination."""
        for i in range(15):
            User.objects.create_user(email=f'user{i+4}@example.com', profile_name=f'user{i+4}', password='pass')
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_profile_list_cache(self):
        """Test profile list caching."""
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get(self.profile_list_url)
        response2 = self.client.get(self.profile_list_url)
        self.assertEqual(response1.data, response2.data)

class ProfileDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', profile_name='testuser', password='testpass123')
        self.other_user = User.objects.create_user(email='otheruser@example.com', profile_name='otheruser', password='testpass123')
        self.profile_detail_url = reverse('profile_detail', kwargs={'user_id': self.user.id})

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()

    def test_retrieve_own_profile(self):
        """Test retrieving own profile."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile_name'], self.user.profile_name)

    def test_retrieve_other_profile(self):
        """Test retrieving another user's profile."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile_name'], self.user.profile_name)

    def test_update_own_profile(self):
        """Test updating own profile."""
        self.client.force_authenticate(user=self.user)
        data = {'bio': 'Updated bio'}
        response = self.client.patch(self.profile_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated bio')

    def test_update_other_profile(self):
        """Test unauthorized update of another user's profile."""
        self.client.force_authenticate(user=self.other_user)
        data = {'bio': 'Unauthorized update'}
        response = self.client.patch(self.profile_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class ProfileTaskTests(TestCase):
    @patch('profiles.tasks.aggregate_popularity_score.delay')
    def test_update_all_popularity_scores(self, mock_aggregate_task):
        """Test updating all popularity scores."""
        user1 = User.objects.create_user(email='user1@example.com', profile_name='user1', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', profile_name='user2', password='pass')
        result = update_all_popularity_scores()
        self.assertEqual(result, f"Initiated popularity score updates for {Profile.objects.count()} profiles")
        self.assertEqual(mock_aggregate_task.call_count, 2)
        mock_aggregate_task.assert_any_call(user1.id)
        mock_aggregate_task.assert_any_call(user2.id)

class ProfileSignalTests(TestCase):
    def test_profile_creation_on_user_creation(self):
        """Test profile creation on user creation."""
        user = User.objects.create_user(email='newuser@example.com', profile_name='newuser', password='pass')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)
        self.assertTrue(PopularityMetrics.objects.filter(user=user).exists())

    def test_follow_count_update_on_follow_creation(self):
        """Test follow count update on follow creation."""
        user1 = User.objects.create_user(email='user1@example.com', profile_name='user1', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', profile_name='user2', password='pass')
        Follow.objects.create(follower=user1, followed=user2)
        user2.profile.refresh_from_db()
        self.assertEqual(user2.profile.follower_count, 1)

    def test_follow_count_update_on_follow_deletion(self):
        """Test follow count update on follow deletion."""
        user1 = User.objects.create_user(email='user1@example.com', profile_name='user1', password='pass')
        user2 = User.objects.create_user(email='user2@example.com', profile_name='user2', password='pass')
        follow = Follow.objects.create(follower=user1, followed=user2)
        follow.delete()
        user2.profile.refresh_from_db()
        self.assertEqual(user2.profile.follower_count, 0)

    def test_validate_image_success(self):
        """Test successful image validation."""
        image_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        image = SimpleUploadedFile("test.gif", image_content, content_type="image/gif")
        validated_image = validate_image(image)
        self.assertEqual(validated_image, image)

    def test_validate_image_invalid_format(self):
        """Test image validation with invalid format."""
        invalid_file = SimpleUploadedFile("test.txt", b"invalid content", content_type="text/plain")
        with self.assertRaises(ValidationError) as context:
            validate_image(invalid_file)
        self.assertIn("Upload a valid image", str(context.exception))

    def test_validate_image_size_limit(self):
        """Test image validation with size limit."""
        large_image_content = b"0" * (2 * 1024 * 1024 + 1)  # 2MB + 1 byte
        large_image = SimpleUploadedFile("large.jpg", large_image_content, content_type="image/jpeg")
        with self.assertRaises(ValidationError) as context:
            validate_image(large_image)
        self.assertIn("Image file too large", str(context.exception))

    @patch('backend.utils.get_image_dimensions')
    def test_validate_image_dimensions(self, mock_get_dimensions):
        """Test image validation with dimensions limit."""
        mock_get_dimensions.return_value = (5000, 5000)
        image = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        with self.assertRaises(ValidationError) as context:
            validate_image(image)
        self.assertIn("Image dimensions too large", str(context.exception))

if __name__ == '__main__':
    unittest.main()