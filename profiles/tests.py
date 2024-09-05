from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from accounts.models import CustomUser
from profiles.models import Profile
from allauth.account.models import EmailAddress
from django.utils.crypto import get_random_string

class ProfileTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile_view_url = reverse('profile_view', kwargs={'user__id': 1})
        cls.update_profile_url = reverse('update_profile')

    def setUp(self):
        self.client = APIClient()

    def generate_unique_email(self, prefix="test"):
        unique_str = get_random_string(8)
        return f"{prefix}_{unique_str}@example.com"

    def test_public_can_view_profile(self):
        user = CustomUser.objects.create_user(
            profile_name="publicprofileuser", email=self.generate_unique_email(), password="StrongPassword123!"
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        profile_view_url = reverse('profile_view', kwargs={'user__id': user.id})

        response = self.client.get(profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], user.profile.bio)

    def test_authenticated_user_can_update_profile(self):
        user = CustomUser.objects.create_user(
            profile_name="profileupdateuser", email="profileupdate@example.com", password="StrongPassword123!"
        )
        self.client.force_authenticate(user=user)

        data = {
            "bio": "Updated bio",
            "location": "Updated location",
            "birth_date": "1990-01-01"
        }
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.bio, "Updated bio")
        self.assertEqual(profile.location, "Updated location")
        self.assertEqual(profile.birth_date.strftime('%Y-%m-%d'), "1990-01-01")

    def test_unauthorized_user_cannot_update_profile(self):
        user1 = CustomUser.objects.create_user(
            profile_name="user1", email="user1@example.com", password="StrongPassword123!"
        )
        user2 = CustomUser.objects.create_user(
            profile_name="user2", email="user2@example.com", password="StrongPassword123!"
        )

        self.client.force_authenticate(user=user2)

        data = {"bio": "Unauthorized update"}
        update_url = reverse('update_profile')

        response = self.client.patch(update_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        profile = Profile.objects.get(user=user1)
        self.assertNotEqual(profile.bio, "Unauthorized update")

    def test_profile_view_for_nonexistent_user(self):
        invalid_profile_view_url = reverse('profile_view', kwargs={'user__id': 9999})
        response = self.client.get(invalid_profile_view_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
