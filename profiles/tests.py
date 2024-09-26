from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from accounts.models import CustomUser
from profiles.models import Profile
from django.utils.crypto import get_random_string
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image

class ProfileTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.update_profile_url = reverse('update_profile')

    def setUp(self):
        self.client = APIClient()

    def generate_unique_email(self, prefix="test"):
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    def test_public_can_view_profile(self):
        user = CustomUser.objects.create_user(
            profile_name="publicprofileuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        profile_view_url = reverse('profile_view', kwargs={'user_id': user.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], user.profile.bio)

    def test_authenticated_user_can_update_profile(self):
        user = CustomUser.objects.create_user(
            profile_name="profileupdateuser",
            email="profileupdate@example.com",
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        self.client.force_authenticate(user=user)
        data = {"bio": "Updated bio"}
        response = self.client.patch(self.update_profile_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.bio, "Updated bio")

    def test_profile_view_for_nonexistent_user(self):
        invalid_profile_view_url = reverse('profile_view', kwargs={'user_id': 9999})
        response = self.client.get(invalid_profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_profile_creation_on_user_registration(self):
        email = self.generate_unique_email()
        user = CustomUser.objects.create_user(
            profile_name="newprofileuser",
            email=email,
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        profile = Profile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user.email, email)

    def test_popularity_score_update_with_ratings(self):
        user = CustomUser.objects.create_user(
            profile_name="popularuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        post = user.posts.create(title="Test Post", content="Content of the test post.")
        post.average_rating = 4.5
        post.total_ratings = 10
        post.save()
        profile = user.profile
        profile.update_popularity_score()
        self.assertGreater(profile.popularity_score, 0)
        self.assertEqual(profile.popularity_score, (4.5 * 0.4) + (10 * 0.3))

    def test_follower_count_updates_on_follow(self):
        user1 = CustomUser.objects.create_user(
            profile_name="user1",
            email=self.generate_unique_email("user1"),
            password="StrongPassword123!"
        )
        user2 = CustomUser.objects.create_user(
            profile_name="user2",
            email=self.generate_unique_email("user2"),
            password="StrongPassword123!"
        )
        user1.is_active = True
        user2.is_active = True
        user1.save()
        user2.save()
        user1.followers.create(follower=user2)
        self.assertEqual(user1.profile.follower_count, 1)

    def test_unauthorized_user_cannot_update_profile(self):
        user1 = CustomUser.objects.create_user(
            profile_name="user1",
            email=self.generate_unique_email("user1"),
            password="StrongPassword123!"
        )
        user2 = CustomUser.objects.create_user(
            profile_name="user2",
            email=self.generate_unique_email("user2"),
            password="StrongPassword123!"
        )
        user1.is_active = True
        user2.is_active = True
        user1.save()
        user2.save()
        self.client.force_authenticate(user=user2)
        update_url = reverse('update_profile')
        data = {"bio": "Unauthorized update attempt"}
        response = self.client.patch(update_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_image_size_limit(self):
        user = CustomUser.objects.create_user(
            profile_name="imagetestuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)
        file = io.BytesIO()
        image = Image.new('RGB', size=(1000, 1000), color='red')
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        file.size = 2 * 1024 * 1024 + 1  # 2MB + 1 byte
        data = {"image": file}
        response = self.client.patch(self.update_profile_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_profile_popularity_score_calculation(self):
        user = CustomUser.objects.create_user(
            profile_name="popularityuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!"
        )
        user.is_active = True
        user.save()
        for i in range(3):
            post = user.posts.create(title=f"Test Post {i}", content=f"Content of test post {i}")
            post.average_rating = 4.0
            post.total_ratings = 5
            post.save()
        for i in range(2):
            follower = CustomUser.objects.create_user(
                profile_name=f"follower{i}",
                email=self.generate_unique_email(f"follower{i}"),
                password="StrongPassword123!"
            )
            user.followers.create(follower=follower)
        user.profile.update_popularity_score()
        expected_score = (4.0 * 0.4) + (15 * 0.3) + (2 * 0.3)
        self.assertAlmostEqual(user.profile.popularity_score, expected_score, places=2)

    def test_profile_serializer_hides_email_for_non_owner(self):
        user1 = CustomUser.objects.create_user(
            profile_name="user1",
            email=self.generate_unique_email("user1"),
            password="StrongPassword123!"
        )
        user2 = CustomUser.objects.create_user(
            profile_name="user2",
            email=self.generate_unique_email("user2"),
            password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user2)
        profile_view_url = reverse('profile_view', kwargs={'user_id': user1.id})
        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('email', response.data)

    def test_profile_update_with_invalid_data(self):
        user = CustomUser.objects.create_user(
            profile_name="invalidupdateuser",
            email=self.generate_unique_email(),
            password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)
        data = {"bio": "A" * 501}  # Bio exceeds max length
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('bio', response.data)
