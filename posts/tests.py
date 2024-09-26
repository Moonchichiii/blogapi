from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()

class PostTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            email='staffuser@example.com',
            profile_name='staffuser',
            password='staffpass123',
            is_staff=True
        )
        self.post1 = Post.objects.create(
            author=self.user,
            title='First Post',
            content='Content for the first post.',
            is_approved=True
        )
        self.post2 = Post.objects.create(
            author=self.user,
            title='Second Post',
            content='Content for the second post.',
            is_approved=False
        )
        self.post_url = reverse('post-list')

    def test_list_posts_as_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'author': 'current'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn(self.post1.title, titles)
        self.assertIn(self.post2.title, titles)

    def test_list_posts_as_unauthenticated_user(self):
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_search_posts_by_title(self):
        response = self.client.get(self.post_url, {'search': 'First'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_create_post(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Post',
            'content': 'Content for the new post.'
        }
        response = self.client.post(self.post_url, data)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(Post.objects.latest('id').title, 'New Post')

    def test_create_post_as_unauthenticated_user(self):
        data = {
            'title': 'Unauthorized Post',
            'content': 'This post should not be created.'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_with_invalid_data(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': '',
            'content': 'Content without a title.'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_post_by_non_owner(self):
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'title': 'Updated Title'
        }
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        response = self.client.patch(post_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_approve_post(self):
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)

    def test_list_posts_with_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'limit': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)

    def test_filter_posts_by_approval_status(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'is_approved': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_delete_post_as_owner(self):
        self.client.force_authenticate(user=self.user)
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        response = self.client.delete(post_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

    def test_delete_post_as_non_owner(self):
        self.client.force_authenticate(user=self.staff_user)
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        response = self.client.delete(post_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_approve_posts(self):
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_approve_post_with_invalid_data(self):
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={'is_approved': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        Post.objects.all().delete()
        User.objects.all().delete()
