from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory
import uuid

from comments.models import Comment
from profiles.models import Profile
from profiles.tasks import update_all_popularity_scores
from ratings.models import Rating
from tags.models import ProfileTag

from .models import Post
from .serializers import PostSerializer


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
        self.factory = APIRequestFactory()

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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Title')

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
        invalid_image = SimpleUploadedFile(
            "image.bmp", image_content, content_type="image/bmp"
        )
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
        post = Post.objects.create(
            author=self.user, title="Test Post", content="Test content"
        )
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

    @transaction.atomic
    def test_post_serializer_perform_update(self):
        """Test post serializer perform update."""
        user = User.objects.create_user(
            email=f'test_update_{uuid.uuid4()}@example.com',
            profile_name=f'testuser_{uuid.uuid4().hex[:8]}',
            password='testpass123'
        )
        post = Post.objects.create(
            author=user, title='Original Post', content='Original content', is_approved=True
        )
        data = {'title': 'Updated Post'}

        request = self.factory.get('/')
        request.user = user

        serializer = PostSerializer(post, data=data, partial=True, context={'request': request})

        self.assertTrue(serializer.is_valid())
        updated_post = serializer.save()
        self.assertEqual(updated_post.title, 'Updated Post')
        self.assertFalse(updated_post.is_approved)

        # Test admin update
        admin_user = User.objects.create_superuser(
            email=f'admin_{uuid.uuid4()}@example.com',
            profile_name=f'admin_{uuid.uuid4().hex[:8]}',
            password='adminpass123'
        )
        data = {'title': 'Admin Updated Post', 'is_approved': True}

        admin_request = self.factory.get('/')
        admin_request.user = admin_user

        serializer = PostSerializer(
            updated_post, data=data, partial=True, context={'request': admin_request}
        )

        self.assertTrue(serializer.is_valid())
        admin_updated_post = serializer.save()
        self.assertEqual(admin_updated_post.title, 'Admin Updated Post')
        self.assertTrue(admin_updated_post.is_approved)

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

        rater2 = User.objects.create_user(
            email='rater2@example.com',
            profile_name='rater2',
            password='raterpass123'
        )
        Profile.objects.get_or_create(user=rater2)

        # Create a post
        post = Post.objects.create(
            author=author,
            title='Test Post',
            content='This is a test post.',
            is_approved=True
        )

        # Add ratings to the post
        Rating.objects.create(post=post, user=rater1, value=4)
        Rating.objects.create(post=post, user=rater2, value=5)

        # Update popularity scores
        update_all_popularity_scores()

        # Refresh the author's profile from the database
        author_profile = Profile.objects.get(user=author)

        # Check if the popularity score has been updated
        self.assertGreater(author_profile.popularity_score, 0)

        # Create another post and add more ratings
        post2 = Post.objects.create(
            author=author,
            title='Second Test Post',
            content='This is another test post.',
            is_approved=True
        )

        Rating.objects.create(post=post2, user=rater1, value=5)
        Rating.objects.create(post=post2, user=rater2, value=5)

        # Update popularity scores again
        update_all_popularity_scores()

        # Refresh the author's profile again
        author_profile.refresh_from_db()

        # Check if the popularity score has increased
        self.assertGreater(author_profile.popularity_score, 0)

        # Optional: Check if the post's average rating is updated
        post.refresh_from_db()
        self.assertEqual(post.average_rating, 4.5)
        post2.refresh_from_db()
        self.assertEqual(post2.average_rating, 5.0)

class PostListViewTests(APITestCase):
    def setUp(self):
        """Set up test data for PostListViewTests."""
        self.user = User.objects.create_user(
            email='user@example.com', profile_name='user', password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            email='staffuser@example.com', profile_name='staff', password='staffpass123', is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            email='admin@example.com', profile_name='admin', password='adminpass123'
        )
        self.post = Post.objects.create(
            author=self.user, title='Test Post', content='Test content', is_approved=True
        )
        self.unapproved_post = Post.objects.create(
            author=self.user, title='Unapproved Post', content='Test content', is_approved=False
        )
        self.post_url = reverse('post-list')

    def test_get_queryset_unauthenticated(self):
        """Test get queryset as unauthenticated user."""
        response = self.client.get(self.post_url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Post')

    def test_get_queryset_authenticated(self):
        """Test get queryset as authenticated user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_queryset_staff(self):
        """Test get queryset as staff user."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.post_url)
        self.assertEqual(len(response.data['results']), 2)

    def test_search_posts_by_title_and_content(self):
        """Search posts by title or content."""
        response = self.client.get(self.post_url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post.title)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        titles = [post['title'] for post in response.data['results']]
        self.assertIn(self.post.title, titles)
        self.assertIn(self.unapproved_post.title, titles)
        
        response = self.client.get(self.post_url, {'search': 'content'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_only_current_user_posts(self):
        """List only the posts created by the current logged-in user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'author': 'current'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_approved_and_non_approved_posts(self):
        """Filter posts by approval status."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'is_approved': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(self.post_url, {'is_approved': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_cache_invalidation_on_update(self):
        """Test that cache is invalidated when a post is updated."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(reverse('post-detail', kwargs={'pk': self.post.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_data = {'title': 'Updated First Post'}
        response = self.client.patch(reverse('post-detail', kwargs={'pk': self.post.id}), updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('post-detail', kwargs={'pk': self.post.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated First Post')
        
    def test_staff_can_edit_other_user_post(self):
        """Test that staff users can edit posts they don't own."""
        self.client.force_authenticate(user=self.staff_user)
        updated_data = {'title': 'Updated by Staff'}
        response = self.client.patch(reverse('post-detail', kwargs={'pk': self.post.id}), updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated by Staff')

    def test_non_staff_cannot_edit_other_user_post(self):
        """Test that non-staff users cannot edit posts they don't own."""
        other_user = User.objects.create_user(
            email='other@example.com', profile_name='other', password='otherpass123'
        )
        self.client.force_authenticate(user=other_user)
        updated_data = {'title': 'Updated by Other User'}
        response = self.client.patch(reverse('post-detail', kwargs={'pk': self.post.id}), updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_functionality_for_authenticated_user(self):
        """Test search functionality for authenticated users."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['title'], self.post.title)

    def test_search_functionality_for_unauthenticated_user(self):
        """Test search functionality for unauthenticated users."""
        self.post.is_approved = True
        self.post.save()
        response = self.client.get(self.post_url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post.title)


class ApprovePostViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com', profile_name='user', password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com', profile_name='admin', password='adminpass123'
        )
        self.staff_user = User.objects.create_user(
            email='staffuser@example.com', profile_name='staff', password='staffpass123', is_staff=True
        )
        self.post1 = Post.objects.create(
            author=self.user, title='First Post', content='Test content', is_approved=False
        )
        self.post_url = reverse('post-list')

    def test_approve_post_as_admin(self):
        """Test approve post as admin."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(reverse('approve-post', kwargs={'pk': self.post1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertTrue(self.post1.is_approved)
        
    def test_approve_post_as_non_admin(self):
        """Test approve post as non-admin."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(reverse('approve-post', kwargs={'pk': self.post1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
