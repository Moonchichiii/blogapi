from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import UserRateThrottle
from django.utils.crypto import get_random_string
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from profiles.models import Profile
from profiles.tasks import update_all_popularity_scores

CustomUser = get_user_model()


class TestThrottle(UserRateThrottle):
    """Custom throttle class for user rate limiting."""
    scope = 'user'


class ProfileTests(APITestCase):
    """Test suite for profile-related API endpoints."""

    @classmethod
    def setUpTestData(cls):
        """Set up URLs for profile-related tests."""
        cls.update_profile_url = reverse('current_user_profile')
        cls.profile_list_url = reverse('profile_list')

    def setUp(self):
        """Initialize the API client for each test."""
        self.client = APIClient()

    def create_user(self, profile_name, email=None, password="StrongPassword123!"):
        """Helper method to create a user with a profile."""
        if email is None:
            email = self.generate_unique_email(profile_name)
        user = CustomUser.objects.create_user(
            profile_name=profile_name,
            email=email,
            password=password
        )
        user.is_active = True
        user.save()
        return user

    def generate_unique_email(self, prefix="test"):
        """Generate a unique email address for testing."""
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    def test_public_can_view_profile(self):
        """Test that the public can view a user's profile."""
        user = self.create_user("publicprofileuser")
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], user.profile.bio)

    def test_authenticated_user_can_update_profile(self):
        """Test that an authenticated user can update their profile."""
        user = self.create_user("profileupdateuser")
        self.client.force_authenticate(user=user)
        data = {"bio": "Updated bio"}
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.bio, "Updated bio")

    def test_unauthorized_user_cannot_update_profile(self):
        """Test that an unauthorized user cannot update another user's profile."""
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        self.client.force_authenticate(user=user2)
        update_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        data = {"bio": "Unauthorized update attempt"}
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_profile_view_for_nonexistent_user(self):
        """Test that viewing a nonexistent user's profile returns a 404."""
        invalid_profile_view_url = reverse('profile_detail', kwargs={'user_id': 9999})
        response = self.client.get(invalid_profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_profile_creation_on_user_registration(self):
        """Test that a profile is created when a new user registers."""
        user = self.create_user("newprofileuser")
        profile = Profile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user.email, user.email)

    def test_popularity_score_update_with_ratings(self):
        """Test that a profile's popularity score updates correctly with ratings."""
        user = self.create_user("popularuser")
        post = user.posts.create(title="Test Post", content="Content of the test post.")
        post.average_rating = 4.5
        post.total_ratings = 10
        post.save()
        profile = user.profile
        profile.update_popularity_score()
        self.assertGreater(profile.popularity_score, 0)
        expected_score = (4.5 * 0.4) + (10 * 0.3) + (profile.follower_count * 0.3)
        self.assertAlmostEqual(profile.popularity_score, expected_score, places=2)

    def test_follower_count_updates_on_follow(self):
        """Test that a profile's follower count updates correctly when followed."""
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        user1.followers.create(follower=user2)
        user1.profile.update_counts()
        self.assertEqual(user1.profile.follower_count, 1)

    def test_profile_list_pagination(self):
        """Test that the profile list endpoint supports pagination."""
        for i in range(25):
            self.create_user(f'user{i}')
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_profile_list_ordering(self):
        """Test that the profile list endpoint supports ordering by popularity score."""
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        user1.profile.popularity_score = 100
        user1.profile.save()
        user2.profile.popularity_score = 50
        user2.profile.save()
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['profile_name'], "user1")
        self.assertEqual(response.data['results'][1]['profile_name'], "user2")

    def test_profile_update_with_invalid_data(self):
        """Test that updating a profile with invalid data returns a 400."""
        user = self.create_user("invalidupdateuser")
        self.client.force_authenticate(user=user)
        data = {"bio": "a" * 501}
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_serializer_hides_email_for_non_owner(self):
        """Test that the profile serializer hides the email for non-owners."""
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_str_representation(self):
        """Test the string representation of a profile."""
        user = self.create_user("strrepuser")
        self.assertEqual(str(user.profile), "strrepuser's profile")

    @patch('profiles.models.Profile.update_all_popularity_scores')
    def test_update_all_popularity_scores(self, mock_update):
        """Test that the update_all_popularity_scores method is called."""
        Profile.update_all_popularity_scores()
        mock_update.assert_called_once()

    def test_is_following_property(self):
        """Test the is_following property of a profile."""
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        user1.followers.create(follower=user2)
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_following'])

    def test_profile_image_url(self):
        """Test that the profile image URL is correctly generated."""
        user = self.create_user("imageurluser")
        self.client.force_authenticate(user=user)
        with patch('cloudinary.CloudinaryImage') as mock_cloudinary:
            mock_cloudinary.return_value.build_url.return_value = (
                'https://res.cloudinary.com/dakjlrean/image/upload/test_image'
            )
            user.profile.image = 'test_image'
            user.profile.save()
            response = self.client.get(self.update_profile_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['image'], 'https://res.cloudinary.com/dakjlrean/image/upload/test_image')

    def test_profile_list_empty(self):
        """Test that the profile list endpoint returns an empty list when there are no profiles."""
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_profile_detail_unauthenticated(self):
        """Test that an unauthenticated user can view a profile without seeing the email."""
        user = self.create_user("unauthuser")
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_clean(self):
        """Test the profile clean method for image size validation."""
        user = CustomUser.objects.create_user(email='test@example.com', profile_name='testuser')
        profile = Profile.objects.get(user=user)
        profile.image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        profile.clean()
        with self.assertRaises(ValidationError):
            profile.image = SimpleUploadedFile(
                "large_image.jpg", b"x" * (2 * 1024 * 1024 + 1), content_type="image/jpeg"
            )
            profile.clean()

    @patch('profiles.tasks.update_all_popularity_scores.delay')
    def test_update_all_popularity_scores_task(self, mock_task):
        """Test that the update_all_popularity_scores task is called."""
        Profile.update_all_popularity_scores()
        mock_task.assert_called_once()


class ProfileTasksTest(TestCase):
    """Test suite for profile-related tasks."""

    @patch('profiles.models.Profile.update_popularity_score')
    def test_update_all_popularity_scores(self, mock_update):
        """Test that the update_all_popularity_scores task updates all profiles."""
        # Create users (profiles will be created automatically via signals)
        user1 = CustomUser.objects.create(email='user1@example.com', profile_name='user1')
        user2 = CustomUser.objects.create(email='user2@example.com', profile_name='user2')

        # Ensure profiles exist
        self.assertTrue(Profile.objects.filter(user=user1).exists())
        self.assertTrue(Profile.objects.filter(user=user2).exists())

        # Call the task
        update_all_popularity_scores()

        # Assert that the update method was called for each profile
        self.assertEqual(mock_update.call_count, Profile.objects.count())
