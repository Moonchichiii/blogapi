from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from .models import Profile
from .serializers import ProfileSerializer
from .tasks import update_all_popularity_scores
from .messages import STANDARD_MESSAGES

User = get_user_model()

class ProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.update_profile_url = reverse('current_user_profile')
        self.profile_list_url = reverse('profile_list')

    def create_user(self, profile_name, email=None, password="StrongPassword123!"):
        if email is None:
            email = f"{profile_name}@example.com"
        user = User.objects.create_user(
            profile_name=profile_name,
            email=email,
            password=password
        )
        user.is_active = True
        user.save()
        return user

    def test_public_can_view_profile(self):
        user = self.create_user("publicprofileuser")
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], user.profile.bio)

    def test_authenticated_user_can_update_profile(self):
        user = self.create_user("profileupdateuser")
        self.client.force_authenticate(user=user)
        data = {"bio": "Updated bio"}
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.bio, "Updated bio")

    def test_unauthorized_user_cannot_update_profile(self):
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        self.client.force_authenticate(user=user2)
        update_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        data = {"bio": "Unauthorized update attempt"}
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_profile_creation_on_user_registration(self):
        user = self.create_user("newprofileuser")
        profile = Profile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user.email, user.email)

    def test_popularity_score_update_with_ratings(self):
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
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        user1.followers.create(follower=user2)
        user1.profile.update_counts()
        self.assertEqual(user1.profile.follower_count, 1)

    def test_profile_list_pagination(self):
        for i in range(25):
            self.create_user(f'user{i}')
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_profile_list_ordering(self):
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
        user = self.create_user("invalidupdateuser")
        self.client.force_authenticate(user=user)
        data = {"bio": "a" * 501}
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('bio', response.data)
        self.assertIn("Ensure this field has no more than 500 characters.", str(response.data['bio'][0]))

    def test_profile_serializer_hides_email_for_non_owner(self):
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_str_representation(self):
        user = self.create_user("strrepuser")
        self.assertEqual(str(user.profile), "strrepuser's profile")

    @patch('profiles.models.Profile.update_all_popularity_scores')
    def test_update_all_popularity_scores(self, mock_update):
        Profile.update_all_popularity_scores()
        mock_update.assert_called_once()

    def test_is_following_property(self):
        user1 = self.create_user("user1")
        user2 = self.create_user("user2")
        user1.followers.create(follower=user2)
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_following'])

    @patch('cloudinary.CloudinaryImage')
    def test_profile_image_url(self, mock_cloudinary):
        user = self.create_user("imageurluser")
        self.client.force_authenticate(user=user)
        mock_cloudinary.return_value.build_url.return_value = 'https://res.cloudinary.com/dakjlrean/image/upload/test_image'
        user.profile.image = 'test_image'
        user.profile.save()
        response = self.client.get(self.update_profile_url)
            
    # Updated assertion to look inside the 'data' key
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data['data'])
        self.assertEqual(response.data['data']['image'], 'https://res.cloudinary.com/dakjlrean/image/upload/test_image')


    def test_profile_detail_unauthenticated(self):
        user = self.create_user("unauthuser")
        profile_view_url = reverse('profile_detail', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_clean(self):
        user = self.create_user("testuser")
        profile = Profile.objects.get(user=user)
        profile.image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        profile.clean()
        with self.assertRaises(ValidationError):
            profile.image = SimpleUploadedFile(
                "large_image.jpg", b"x" * (2 * 1024 * 1024 + 1), content_type="image/jpeg"
            )
            profile.clean()

class ProfileTasksTest(TestCase):
    @patch('profiles.models.Profile.update_popularity_score')
    def test_update_all_popularity_scores(self, mock_update):
        User.objects.create_user(profile_name='user1', email='user1@example.com', password='testpass123')
        User.objects.create_user(profile_name='user2', email='user2@example.com', password='testpass123')
        
        update_all_popularity_scores()
        
        self.assertEqual(mock_update.call_count, Profile.objects.count())

class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.profile = self.user.profile

    def test_profile_creation(self):
        self.assertIsNotNone(self.profile)
        self.assertEqual(str(self.profile), "testuser's profile")

    def test_update_popularity_score(self):
        self.profile.update_popularity_score()
        self.assertEqual(self.profile.popularity_score, 0)  # No posts or followers yet

    def test_update_counts(self):
        self.profile.update_counts()
        self.assertEqual(self.profile.follower_count, 0)
        self.assertEqual(self.profile.following_count, 0)
        self.assertEqual(self.profile.comment_count, 0)
        self.assertEqual(self.profile.tag_count, 0)

    def test_clean_method(self):
        small_image = SimpleUploadedFile("small.jpg", b"file_content", content_type="image/jpeg")
        self.profile.image = small_image
        self.profile.clean()  # Should not raise an error

        large_image = SimpleUploadedFile("large.jpg", b"x" * (2 * 1024 * 1024 + 1), content_type="image/jpeg")
        self.profile.image = large_image
        with self.assertRaises(ValidationError):
            self.profile.clean()

class ProfileSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.profile_data = {
            'bio': 'Test bio',
            'image': None,
        }

    def test_contains_expected_fields(self):
        serializer = ProfileSerializer(instance=self.user.profile)
        data = serializer.data
        self.assertCountEqual(data.keys(), ['id', 'user_id', 'bio', 'image', 'follower_count', 'following_count',
                                            'popularity_score', 'is_following', 'profile_name', 'email',
                                            'comment_count', 'tag_count'])

    def test_bio_field_content(self):
        serializer = ProfileSerializer(data=self.profile_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['bio'], 'Test bio')

class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.profile = self.user.profile
        self.profile_list_url = reverse('profile_list')
        self.profile_detail_url = reverse('profile_detail', kwargs={'user_id': self.user.id})
        self.current_user_profile_url = reverse('current_user_profile')

    def test_get_profile_list(self):
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['message'])

    def test_get_profile_detail(self):
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile_name'], 'testuser')

    def test_update_current_user_profile(self):
        self.client.force_authenticate(user=self.user)
        data = {'bio': 'Updated bio'}
        response = self.client.patch(self.current_user_profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio')

    def test_get_nonexistent_profile(self):
        non_existent_url = reverse('profile_detail', kwargs={'user_id': 9999})
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class ProfileSignalTests(TestCase):
    def test_profile_creation_signal(self):
        user = User.objects.create_user(profile_name='testuser', email='test@example.com', password='testpass123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)

class ProfilePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(profile_name='user1', email='user1@example.com', password='testpass123')
        self.user2 = User.objects.create_user(profile_name='user2', email='user2@example.com', password='testpass123')
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
       
    def test_user_can_update_own_profile(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('current_user_profile')
        data = {'bio': 'Updated bio for user1'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.bio, 'Updated bio for user1')
