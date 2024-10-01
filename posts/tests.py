from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from comments.models import Comment
from ratings.models import Rating
from .models import Post
from django.contrib.contenttypes.models import ContentType
from tags.models import ProfileTag

User = get_user_model()


class PostTests(APITestCase):
    """Test suite for the Post model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='otheruser@example.com',
            profile_name='otheruser',
            password='otherpass123'
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
        """List posts as authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'author': 'current'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn(self.post1.title, titles)
        self.assertIn(self.post2.title, titles)

    def test_list_posts_as_unauthenticated_user(self):
        """List posts as unauthenticated user."""
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_search_posts_by_title(self):
        """Search posts by title."""
        response = self.client.get(self.post_url, {'search': 'First'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_create_post(self):
        """Create a new post."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Post',
            'content': 'Content for the new post.'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(Post.objects.latest('id').title, 'New Post')

    def test_create_post_as_unauthenticated_user(self):
        """Create post as unauthenticated user."""
        data = {
            'title': 'Unauthorized Post',
            'content': 'This post should not be created.'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_with_invalid_data(self):
        """Create post with invalid data."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': '',
            'content': 'Content without a title.'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_post_by_non_owner(self):
        """Update post by non-owner."""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'title': 'Updated Title'
        }
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        response = self.client.patch(post_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_approve_post(self):
        """Admin approve post."""
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)

    def test_list_posts_with_pagination(self):
        """List posts with pagination."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'limit': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)

    def test_filter_posts_by_approval_status(self):
        """Filter posts by approval status."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'is_approved': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_delete_post_as_owner(self):
        """Delete post as owner."""
        self.client.force_authenticate(user=self.user)
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        response = self.client.delete(post_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

    def test_delete_post_as_non_owner(self):
        """Delete post as non-owner."""
        self.client.force_authenticate(user=self.staff_user)
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        response = self.client.delete(post_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_approve_posts(self):
        """Unauthenticated user cannot approve posts."""
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_approve_post_with_invalid_data(self):
        """Approve post with invalid data."""
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={'is_approved': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_approve_post_as_non_admin(self):
        """Non-admin user cannot approve posts."""
        self.client.force_authenticate(user=self.user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_disapprove_post_without_reason(self):
        """Cannot disapprove post without reason."""
        self.client.force_authenticate(user=self.staff_user)
        disapprove_url = reverse('disapprove-post', kwargs={'pk': self.post2.id})
        response = self.client.post(disapprove_url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Disapproval reason is required", response.data['error'])

    def test_create_post_with_disallowed_image_extension(self):
        """Create post with disallowed image extension."""
        self.client.force_authenticate(user=self.user)
        image_content = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x01\x00\x2C\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
        )
        invalid_image = SimpleUploadedFile("image.bmp", image_content, content_type="image/bmp")
        data = {
            'title': 'New Post with Invalid Image Extension',
            'content': 'Content for the new post.',
            'image': invalid_image
        }
        response = self.client.post(self.post_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid image format", response.data['image'])

    def test_edit_post_but_cannot_change_approval_status(self):
        """Edit post but cannot change approval status."""
        self.client.force_authenticate(user=self.user)
        post_detail_url = reverse('post-detail', kwargs={'pk': self.post1.id})
        data = {
            'title': 'New Title',
            'is_approved': True
        }
        response = self.client.patch(post_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, "New Title")
        self.assertFalse(self.post1.is_approved)

    def test_post_creation_with_tags(self):
        """Test post creation with tags."""
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Test Post with Tags",
            "content": "This is a test post with tags.",
            "tags": [self.other_user.profile_name]
        }
        response = self.client.post(reverse('post-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(title="Test Post with Tags")
        self.assertEqual(
            ProfileTag.objects.filter(content_type__model='post', object_id=post.id).count(), 1
        )

    def test_post_deletion_cascades(self):
        """Test post deletion cascades."""
        self.client.force_authenticate(user=self.user)
        post = Post.objects.create(author=self.user, title="Test Post", content="Test content")
        Comment.objects.create(post=post, author=self.other_user, content="Test comment")
        Rating.objects.create(post=post, user=self.other_user, value=4)
        content_type = ContentType.objects.get_for_model(Post)
        ProfileTag.objects.create(
            tagged_user=self.other_user,
            tagger=self.user,
            content_type=content_type,
            object_id=post.id
        )
        response = self.client.delete(reverse('post-detail', kwargs={'pk': post.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(Rating.objects.count(), 0)
        self.assertEqual(ProfileTag.objects.count(), 0)

    def test_post_serializer_perform_update(self):
        """Test post serializer perform update."""
        user = User.objects.create_user(email='test@example.com', profile_name='testuser')
        post = Post.objects.create(title='Test Post', content='Test content', author=user)
        data = {'title': 'Updated Post'}
        serializer = PostSerializer(post, data=data, partial=True, context={'request': MockRequest(user=user)})

        self.assertTrue(serializer.is_valid())
        updated_post = serializer.save()
        self.assertEqual(updated_post.title, 'Updated Post')
        self.assertFalse(updated_post.is_approved)

    def test_post_detail_retrieve(self):
        """Test post detail retrieve."""
        post = Post.objects.create(title='Test Post', content='Test content', author=self.user, is_approved=True)
        url = reverse('post-detail', kwargs={'pk': post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Post')

    def test_disapprove_post(self):
        """Test disapprove post."""
        self.client.force_authenticate(user=self.staff_user)
        post = Post.objects.create(title='Test Post', content='Test content', author=self.user, is_approved=True)
        url = reverse('disapprove-post', kwargs={'pk': post.id})
        data = {'reason': 'Inappropriate content'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertFalse(post.is_approved)

    def tearDown(self):
        """Clean up after tests."""
        Post.objects.all().delete()
        User.objects.all().delete()
