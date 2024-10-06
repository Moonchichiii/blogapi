from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import Profile
from .serializers import ProfileSerializer
from .tasks import update_all_popularity_scores
from posts.tasks import update_post_stats
from .messages import STANDARD_MESSAGES  
from posts.models import Post

User = get_user_model()


class ProfileTests(TestCase):
    """Test suite for Profile-related functionalities."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.update_profile_url = reverse('current_user_profile')
        self.profile_list_url = reverse('profile_list')
        self.user = self._create_user("testuser")
        self.user1 = self._create_user("user1")
        self.user2 = self._create_user("user2")
        self.post1 = Post.objects.create(author=self.user1, title="Test Post 1", content="Test content 1")
        self.post2 = Post.objects.create(author=self.user2, title="Test Post 2", content="Test content 2")
        
        
    def _create_user(self, profile_name: str, email: str = None, password: str = "StrongPassword123!") -> User:
        """Helper method to create a user."""
        if email is None:
            email = f"{profile_name}_{User.objects.count()}@example.com"
            user = User.objects.create_user(
                profile_name=f"{profile_name}_{User.objects.count()}",
                email=email,
                password=password
                )
            user.is_active = True
            user.save()
            return user
        
        
    def test_public_can_view_profile(self) -> None:
        """Test that public users can view profiles."""
        user = self._create_user("publicprofileuser")
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], user.profile.bio)

    def test_authenticated_user_can_update_profile(self) -> None:
        """Test that authenticated users can update their profiles."""
        user = self._create_user("profileupdateuser")
        self.client.force_authenticate(user=user)
        data = {"bio": "Updated bio"}
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.bio, "Updated bio")

    def test_unauthorized_user_cannot_update_profile(self) -> None:
        """Test that unauthorized users cannot update other users' profiles."""
        user1 = self._create_user("user1")
        user2 = self._create_user("user2")
        self.client.force_authenticate(user=user2)
        update_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        data = {"bio": "Unauthorized update attempt"}
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_profile_creation_on_user_registration(self) -> None:
        """Test that a profile is created when a user registers."""
        user = self._create_user("newprofileuser")
        profile = Profile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user.email, user.email)

    def test_popularity_score_update_with_ratings(self) -> None:
        """Test that the popularity score updates correctly with ratings."""
        user = self._create_user("popularuser")
        post = user.posts.create(title="Test Post", content="Content of the test post.", is_approved=True)
        post.average_rating = 4.5
        post.total_ratings = 10
        post.save()
        profile = user.profile
        profile.update_popularity_score()
        expected_score = (
            (4.5 * 0.3) +
            (10 * 0.2) +
            (0 * 0.1) +
            (0 * 0.1) +
            (0 * 0.3)
        )
        self.assertAlmostEqual(profile.popularity_score, expected_score, places=2)

    def test_follower_count_updates_on_follow(self) -> None:
        """Test that the follower count updates correctly when a user is followed."""
        user1 = self._create_user("user1")
        user2 = self._create_user("user2")
        user1.followers.create(follower=user2)
        user1.profile.update_counts()
        self.assertEqual(user1.profile.follower_count, 1)

    def test_profile_list_pagination(self) -> None:
        """Test that the profile list is paginated correctly."""
        for i in range(25):
            self._create_user(f'user{i}')
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_profile_list_ordering(self) -> None:
        """Test that the profile list is ordered by popularity score."""
        user1 = self._create_user("user1")
        user2 = self._create_user("user2")
        user1.profile.popularity_score = 100
        user1.profile.save()
        user2.profile.popularity_score = 50
        user2.profile.save()
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['results'][0]['profile_name'].startswith("user1"))
        self.assertTrue(response.data['results'][1]['profile_name'].startswith("user2"))

    def test_profile_update_with_invalid_data(self) -> None:
        """Test that updating a profile with invalid data returns an error."""
        user = self._create_user("invalidupdateuser")
        self.client.force_authenticate(user=user)
        data = {"bio": "a" * 501}
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('bio', response.data)
        self.assertIn("Ensure this field has no more than 500 characters.", str(response.data['bio'][0]))

    def test_profile_serializer_hides_email_for_non_owner(self) -> None:
        """Test that the profile serializer hides the email for non-owners."""
        user1 = self._create_user("user1")
        user2 = self._create_user("user2")
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_str_representation(self) -> None:
        user = self._create_user("strrepuser")
        self.assertEqual(str(user.profile), f"{user.profile_name}'s profile")

    @patch('profiles.models.Profile.update_all_popularity_scores')
    def test_update_all_popularity_scores(self, mock_update) -> None:
        """Test that the update_all_popularity_scores task is called correctly."""
        Profile.update_all_popularity_scores()
        mock_update.assert_called_once()

    def test_is_following_property(self) -> None:
        """Test the is_following property of the profile."""
        user1 = self._create_user("user1")
        user2 = self._create_user("user2")
        user1.followers.create(follower=user2)
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_following'])

    @patch('cloudinary.CloudinaryImage')
    def test_profile_image_url(self, mock_cloudinary) -> None:
        """Test that the profile image URL is generated correctly."""
        user = self._create_user("imageurluser")
        self.client.force_authenticate(user=user)
        mock_cloudinary.return_value.build_url.return_value = 'https://res.cloudinary.com/dakjlrean/image/upload/test_image'
        user.profile.image = 'test_image'
        user.profile.save()
        response = self.client.get(self.update_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data['data'])
        self.assertEqual(response.data['data']['image'], 'https://res.cloudinary.com/dakjlrean/image/upload/test_image')

    def test_profile_detail_unauthenticated(self) -> None:
        """Test that unauthenticated users can view profile details."""
        user = self._create_user("unauthuser")
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_clean(self) -> None:
        """Test the clean method of the profile model."""
        user = self._create_user("testuser")
        profile = Profile.objects.get(user=user)
        profile.image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        profile.clean()
        with self.assertRaises(ValidationError):
            profile.image = SimpleUploadedFile(
                "large_image.jpg", b"x" * (2 * 1024 * 1024 + 1), content_type="image/jpeg"
            )
            profile.clean()


class ProfileTasksTest(TestCase):
    """Test suite for Profile-related tasks."""

    @patch('profiles.models.Profile.update_popularity_score')
    def test_update_all_popularity_scores(self, mock_update) -> None:
        """Test that the update_all_popularity_scores task updates all profiles."""
        User.objects.create_user(profile_name='user1', email='user1@example.com', password='testpass123')
        User.objects.create_user(profile_name='user2', email='user2@example.com', password='testpass123')
        update_all_popularity_scores()
        self.assertEqual(mock_update.call_count, Profile.objects.count())


class ProfileModelTests(TestCase):
    """Test suite for Profile model."""

    def setUp(self) -> None:
        """Set up the test user and profile."""
        self.user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.profile = self.user.profile

    def test_profile_creation(self) -> None:
        """Test that a profile is created correctly."""
        self.assertIsNotNone(self.profile)
        self.assertEqual(str(self.profile), "testuser's profile")

    def test_update_popularity_score(self) -> None:
        """Test that the popularity score updates correctly."""
        self.profile.update_popularity_score()
        self.assertEqual(self.profile.popularity_score, 0) 

    def test_update_counts(self) -> None:
        """Test that the follower, following, comment, and tag counts update correctly."""
        self.profile.update_counts()
        self.assertEqual(self.profile.follower_count, 0)
        self.assertEqual(self.profile.following_count, 0)
        self.assertEqual(self.profile.comment_count, 0)
        self.assertEqual(self.profile.tag_count, 0)

    def test_clean_method(self) -> None:
        """Test the clean method for image size validation."""
        small_image = SimpleUploadedFile("small.jpg", b"file_content", content_type="image/jpeg")
        self.profile.image = small_image
        self.profile.clean()

        large_image = SimpleUploadedFile("large.jpg", b"x" * (2 * 1024 * 1024 + 1), content_type="image/jpeg")
        self.profile.image = large_image
        with self.assertRaises(ValidationError):
            self.profile.clean()


class ProfileSerializerTests(TestCase):
    """Test suite for Profile serializer."""

    def setUp(self) -> None:
        """Set up the test user and profile data."""
        self.user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.profile_data = {
            'bio': 'Test bio',
            'image': None,
        }

    def test_contains_expected_fields(self) -> None:
        """Test that the serializer contains the expected fields."""
        serializer = ProfileSerializer(instance=self.user.profile)
        data = serializer.data
        self.assertCountEqual(data.keys(), [
            'id', 'user_id', 'bio', 'image', 'follower_count', 'following_count',
            'popularity_score', 'is_following', 'profile_name', 'email',
            'comment_count', 'tag_count'
        ])

    def test_bio_field_content(self) -> None:
        """Test that the bio field content is serialized correctly."""
        serializer = ProfileSerializer(data=self.profile_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bio'], 'Test bio')


class ProfileViewTests(TestCase):
    """Test suite for Profile views."""

    def setUp(self) -> None:
        """Set up the test client and URLs."""
        self.client = APIClient()
        self.user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.profile = self.user.profile
        self.profile_list_url = reverse('profile_list')
        self.profile_detail_url = reverse('profile_detail', kwargs={'user_id': self.user.id})
        self.current_user_profile_url = reverse('current_user_profile')

    def test_get_profile_list(self) -> None:
        """Test that the profile list is retrieved correctly."""
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['message'])

    def test_get_profile_detail(self) -> None:
        """Test that the profile detail is retrieved correctly."""
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile_name'], 'testuser')

    def test_update_current_user_profile(self) -> None:
        """Test that the current user can update their profile."""
        self.client.force_authenticate(user=self.user)
        data = {'bio': 'Updated bio'}
        response = self.client.patch(self.current_user_profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio')

    def test_get_nonexistent_profile(self) -> None:
        """Test that retrieving a nonexistent profile returns a 404 error."""
        non_existent_url = reverse('profile_detail', kwargs={'user_id': 9999})
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileSignalTests(TestCase):
    """Test suite for Profile signals."""

    def test_profile_creation_signal(self) -> None:
        """Test that a profile is created when a user is created."""
        user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)


class ProfilePermissionTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.user1 = User.objects.create_user(profile_name='user1', email='user1@example.com', password='testpass123')
        self.user2 = User.objects.create_user(profile_name='user2', email='user2@example.com', password='testpass123')
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
        self.post1 = Post.objects.create(author=self.user1, title="Test Post 1", content="Test content 1")
        self.post2 = Post.objects.create(author=self.user2, title="Test Post 2", content="Test content 2")

    def test_user_can_update_own_profile(self) -> None:
        """Test that a user can update their own profile."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('current_user_profile')
        data = {'bio': 'Updated bio for user1'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.bio, 'Updated bio for user1')

    def test_update_post_stats_success(self) -> None:
        """Test that post statistics update correctly."""
        self.post1.ratings.create(user=self.user2, value=5)
        update_post_stats(self.post1.id)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.average_rating, 5.0)

        # Test with no ratings
        self.post2.update_rating_statistics()
        self.assertEqual(self.post2.average_rating, 0)