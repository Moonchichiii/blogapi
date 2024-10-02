from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from .models import Post
from .serializers import PostSerializer
from .messages import STANDARD_MESSAGES
from profiles.models import Profile
from ratings.models import Rating
from tags.models import ProfileTag
from profiles.tasks import update_all_popularity_scores

User = get_user_model()

class PostTests(APITestCase):
    """Test suite for the Post model and related views."""

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
        self.post_detail_url = lambda pk: reverse('post-detail', kwargs={'pk': pk})
        self.factory = APIRequestFactory()

    def test_list_posts_as_authenticated_user(self):
        """List posts as authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'author': 'current'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Adjust check for paginated data
        if hasattr(response.data, 'count'):
            self.assertEqual(response.data['count'], 2)
        else:
            self.assertEqual(len(response.data['results']), 2)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn(self.post1.title, titles)
        self.assertIn(self.post2.title, titles)
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POSTS_RETRIEVED_SUCCESS']['message'])

    def test_list_posts_as_unauthenticated_user(self):
        """List posts as unauthenticated user."""
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only approved post
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POSTS_RETRIEVED_SUCCESS']['message'])

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
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POST_CREATED_SUCCESS']['message'])

    def test_update_post_by_non_owner(self):
        """Update post by non-owner."""
        self.client.force_authenticate(user=self.staff_user)
        data = {'title': 'Updated Title'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Title')
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POST_UPDATED_SUCCESS']['message'])

    def test_admin_approve_post(self):
        """Admin approve post."""
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POST_APPROVED_SUCCESS']['message'])

    def test_admin_can_disapprove_post(self):
        """Test that only admins can disapprove a post."""
        self.client.force_authenticate(user=self.staff_user)
        disapprove_url = reverse('disapprove-post', kwargs={'pk': self.post1.id})
        data = {'reason': 'Inappropriate content'}
        response = self.client.post(disapprove_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)
        self.assertIn('The post has been disapproved and the author has been notified.', response.data['message'])

    def test_post_ratings_affect_popularity_scores(self):
        """Test that post ratings affect user popularity scores."""
        author = User.objects.create_user(
            email='author@example.com',
            profile_name='author',
            password='authorpass123'
        )
        Profile.objects.get_or_create(user=author)

        rater1 = User.objects.create_user(
            email='rater1@example.com',
            profile_name='rater1',
            password='raterpass123'
        )
        Profile.objects.get_or_create(user=rater1)

        post = Post.objects.create(
            author=author,
            title='Test Post',
            content='This is a test post.',
            is_approved=True
        )

        Rating.objects.create(post=post, user=rater1, value=4)

        # Simulate update of popularity scores via task
        update_all_popularity_scores()

        author_profile = Profile.objects.get(user=author)
        self.assertGreater(author_profile.popularity_score, 0)

    def test_create_post_with_tags(self):
        """Test creating a post with tags."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Tagged Post',
            'content': 'Content for the tagged post.',
            'tags': [self.other_user.profile_name]
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POST_CREATED_SUCCESS']['message'])

    def test_update_post_by_non_owner(self):
        """Non-owner attempting to update a post."""
        self.client.force_authenticate(user=self.other_user)
        data = {'title': 'Unauthorized Update'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_approve_post(self):
        """Admin approving a post."""
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)
        if 'message' in response.data:
            self.assertEqual(response.data['message'], STANDARD_MESSAGES['POST_APPROVED_SUCCESS']['message'])

    def test_update_post_as_owner(self):
        """Owner can update their own post."""
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Updated by Owner'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated by Owner')

    def test_update_post_as_non_owner(self):
        """Non-owner cannot update another user's post."""
        self.client.force_authenticate(user=self.other_user)
        data = {'title': 'Unauthorized Update'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post_as_owner(self):
        """Owner can delete their own post."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())

    def test_delete_post_as_non_owner(self):
        """Non-owner cannot delete another user's post."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(id=self.post1.id).exists())

    def test_visibility_of_approved_posts(self):
        """Only approved posts are visible to unauthenticated users."""
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only one approved post
        self.assertEqual(response.data['results'][0]['title'], self.post1.title)

    def test_visibility_of_non_approved_posts_by_owner(self):
        """Owner can see their non-approved posts."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'author': 'current'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Owner can see both posts

    def test_visibility_of_non_approved_posts_by_admin(self):
        """Admin can see non-approved posts."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_approve_post(self):
        """Admin can approve posts."""
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)

    def test_non_admin_cannot_approve_post(self):
        """Non-admin cannot approve posts."""
        self.client.force_authenticate(user=self.user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_post_ratings_affect_popularity_scores(self):
        """Test that post ratings affect user popularity scores."""
        author = User.objects.create_user(
            email='author@example.com',
            profile_name='author',
            password='authorpass123'
        )
        Profile.objects.get_or_create(user=author)

        rater1 = User.objects.create_user(
            email='rater1@example.com',
            profile_name='rater1',
            password='raterpass123'
        )
        Profile.objects.get_or_create(user=rater1)

        post = Post.objects.create(
            author=author,
            title='Test Post',
            content='This is a test post.',
            is_approved=True
        )

        Rating.objects.create(post=post, user=rater1, value=4)

        # Simulate update of popularity scores via task
        update_all_popularity_scores()

        author_profile = Profile.objects.get(user=author)
        self.assertGreater(author_profile.popularity_score, 0)

    def test_create_post_with_invalid_image(self):
        """Test post creation with an invalid image format."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Invalid Image Post',
            'content': 'This post has an invalid image.',
            'image': SimpleUploadedFile("invalid_image.txt", b"file_content")
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_create_post_with_duplicate_tags(self):
        """Test creating a post with duplicate tags."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Duplicate Tag Post',
            'content': 'This post has duplicate tags.',
            'tags': ['testuser', 'testuser']
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Duplicate tags are not allowed.', str(response.data))

    def test_admin_can_disapprove_post(self):
        """Test that only admins can disapprove a post."""
        self.client.force_authenticate(user=self.staff_user)
        disapprove_url = reverse('disapprove-post', kwargs={'pk': self.post1.id})
        data = {'reason': 'Inappropriate content'}
        response = self.client.post(disapprove_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)
        self.assertIn('POST_DISAPPROVED_SUCCESS', response.data['message'])

    def test_non_admin_cannot_disapprove_post(self):
        """Test that non-admins cannot disapprove posts."""
        self.client.force_authenticate(user=self.user)
        disapprove_url = reverse('disapprove-post', kwargs={'pk': self.post1.id})
        response = self.client.post(disapprove_url, data={'reason': 'Inappropriate content'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_posts_with_pagination(self):
        """Test post listing with pagination."""
        for i in range(11):
            Post.objects.create(
                author=self.user,
                title=f'Post {i+3}',
                content=f'Content for post {i+3}',
                is_approved=True
            )
        response = self.client.get(self.post_url, {'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('next', response.data)

    def test_serializer_invalid_image(self):
        """Test the serializer rejects invalid image formats."""
        data = {
            'title': 'Invalid Image Post',
            'content': 'This post has an invalid image.',
            'image': SimpleUploadedFile("invalid_image.txt", b"file_content")
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Upload a valid image', str(serializer.errors['image'][0]))

    def test_serializer_duplicate_tags(self):
        """Test serializer catches duplicate tags."""
        data = {
            'title': 'Tagged Post',
            'content': 'Content for the tagged post.',
            'tags': ['testuser', 'testuser']
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('DUPLICATE_TAG_ERROR', serializer.errors['tags'][0])

    def test_get_user_rating(self):
        """Test retrieving user rating for a post."""
        self.client.force_authenticate(user=self.user)
        post = Post.objects.create(
            author=self.other_user,
            title='Rated Post',
            content='Content for the rated post.',
            is_approved=True
        )
        Rating.objects.create(post=post, user=self.user, value=5)
        response = self.client.get(self.post_detail_url(post.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_rating']['value'], 5)

    def test_is_owner_field_in_serializer(self):
        """Test that 'is_owner' is set correctly in the serializer."""
        post = Post.objects.create(
            author=self.user,
            title='Owner Test Post',
            content='Content for the post.',
            is_approved=True
        )
        response = self.client.get(self.post_detail_url(post.id))
        self.assertTrue(response.data['is_owner'])

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.post_detail_url(post.id))
        self.assertFalse(response.data['is_owner'])

    def test_list_posts_with_pagination(self):
        """Test post listing with pagination."""
        for i in range(11):
            Post.objects.create(
                author=self.user,
                title=f'Post {i+3}',
                content=f'Content for post {i+3}',
                is_approved=True
            )
        response = self.client.get(self.post_url, {'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        # Check if 'next' exists when there are more than one page#
        if response.data['count'] > 10:
            self.assertIn('next', response.data)

    def test_get_user_rating(self):
        """Test retrieving user rating for a post."""
        self.client.force_authenticate(user=self.user)
        post = Post.objects.create(
            author=self.other_user,
            title='Rated Post',
            content='Content for the rated post.',
            is_approved=True
        )
        Rating.objects.create(post=post, user=self.user, value=5)
        response = self.client.get(self.post_detail_url(post.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_rating', response.data)
        self.assertEqual(response.data['user_rating']['value'], 5)

    def test_is_owner_field_in_serializer(self):
        """Test that 'is_owner' is set correctly in the serializer."""
        post = Post.objects.create(
            author=self.user,
            title='Owner Test Post',
            content='Content for the post.',
            is_approved=True
        )
        response = self.client.get(self.post_detail_url(post.id))
        self.assertIn('is_owner', response.data)
        self.assertTrue(response.data['is_owner'])

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.post_detail_url(post.id))
        self.assertIn('is_owner', response.data)
        self.assertFalse(response.data['is_owner'])
