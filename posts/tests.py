from django.core.cache import cache
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from .models import Post
from .serializers import PostSerializer, PostListSerializer
from tags.models import ProfileTag


from profiles.tasks import update_all_popularity_scores
from comments.models import Comment


from django.core import mail




from django.test import TestCase
from posts.tasks import update_post_stats
from posts.models import Post


from posts.messages import STANDARD_MESSAGES




User = get_user_model()

class PostTests(APITestCase):
    """
    Test suite for post-related functionalities.
    """

    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
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
        is_staff=True,
        is_superuser=True
    )
        now = timezone.now()
        self.post1 = Post.objects.create(
        author=self.user,
        title='First Post',
        content='Content for the first post.',
        is_approved=True,
        )
        self.post1.created_at = now - timedelta(minutes=2)
        self.post1.save()
        
        self.post2 = Post.objects.create(
        author=self.user,
        title='Second Post',
        content='Content for the second post.',
        is_approved=False,
    )
        self.post2.created_at = now - timedelta(minutes=1)
        self.post2.save()
        self.client = APIClient()
        self.post_url = reverse('post-list')
        self.post_detail_url = lambda pk: reverse('post-detail', kwargs={'pk': pk}) 
        self.post_preview_url = reverse('post-previews')

        
    def test_list_posts(self):
        """List posts for different user types."""
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'First Post')
        self.assertEqual(response.data['message'], STANDARD_MESSAGES['POSTS_RETRIEVED_SUCCESS']['message'])

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_post_with_duplicate_tags(self):
        """Test creating a post with duplicate tags."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Duplicate Tagged Post',
            'content': 'Content for the duplicate tagged post.',
            'tags': [self.other_user.profile_name, self.other_user.profile_name]
            }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tags', response.data['errors'])
        error_message = str(response.data['errors']['tags'][0])
        self.assertIn('Duplicate tags are not allowed.', error_message)


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
        self.assertEqual(ProfileTag.objects.count(), 1)
        self.assertEqual(response.data['message'], "Your post has been created successfully.")
        self.assertEqual(Post.objects.latest('id').author, self.user)

    def test_create_post_with_duplicate_tags(self):
        """Test creating a post with duplicate tags."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Duplicate Tagged Post',
            'content': 'Content for the duplicate tagged post.',
            'tags': [self.other_user.profile_name, self.other_user.profile_name]
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Failed to create the post. Please check the provided data.")
        self.assertIn('tags', response.data['errors'])
        self.assertIn('Duplicate tags are not allowed.', response.data['errors']['tags'])

    def test_create_post_with_invalid_image(self):
        """Test creating a post with an invalid image."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Invalid Image Post',
            'content': 'This post has an invalid image.',
            'image': SimpleUploadedFile("invalid_image.txt", b"file_content")
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Failed to create the post. Please check the provided data.")
        self.assertIn('image', response.data['errors'])
        self.assertIn('Upload a valid image.', str(response.data['errors']['image']))

    def test_update_post_as_non_owner(self):
        """Test updating a post as a non-owner."""
        self.client.force_authenticate(user=self.other_user)
        data = {'title': 'Unauthorized Update'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "You do not have permission to perform this action.")


    def test_delete_post_as_non_owner(self):
        """Test deleting a post as a non-owner."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], "You do not have permission to perform this action.")




    def test_delete_post(self):
        """Test deleting a post."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.filter(id=self.post1.id).count(), 0)

    def test_approve_post(self):
        """Test approving a post."""
        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': self.post2.id})
        response = self.client.patch(approve_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)
        self.assertEqual(response.data['message'], "The post has been approved successfully.")

    def test_disapprove_post(self):
        """Test disapproving a post."""
        self.client.force_authenticate(user=self.staff_user)
        disapprove_url = reverse('disapprove-post', kwargs={'pk': self.post1.id})
        data = {'reason': 'Inappropriate content'}
        response = self.client.post(disapprove_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)
        self.assertEqual(response.data['message'], "The post has been disapproved and the author has been notified.")

    def test_disapprove_post_without_reason(self):
        """Test disapproving a post without providing a reason."""
        self.client.force_authenticate(user=self.staff_user)
        disapprove_url = reverse('disapprove-post', kwargs={'pk': self.post1.id})
        response = self.client.post(disapprove_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Disapproval reason is required.")

    def test_rating_updates_profile_popularity(self):
        """Rating a post updates the author's profile popularity score."""
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post1.id, 'value': 5}
        response = self.client.post(reverse('create-update-rating'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post1.update_rating_stats()
        self.user.profile.update_popularity_score()
        self.user.profile.refresh_from_db()
        self.assertGreater(self.user.profile.popularity_score, 0)

        
    def test_post_serializer(self):
        """Test the PostSerializer."""
        serializer = PostSerializer(instance=self.post1, context={'request': None})
        self.assertEqual(serializer.data['title'], self.post1.title)
        self.assertEqual(serializer.data['author'], self.user.profile_name)

    def test_post_list_serializer(self):
        """Test the PostListSerializer."""
        serializer = PostListSerializer(instance=self.post1, context={'request': None})
        self.assertIn('author', serializer.data)
        self.assertIn('comment_count', serializer.data)
        self.assertIn('tag_count', serializer.data)

    def test_post_detail_view(self):
        """Test retrieving a post detail view."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], self.post1.title)
        self.assertTrue(response.data['data']['is_owner'])
        self.assertEqual(response.data['message'], "Post has been retrieved successfully.")

    def test_post_list_view_pagination(self):
        """Test pagination in the post list view."""
        # Create additional posts
        for i in range(15):
            Post.objects.create(
                author=self.user,
                title=f'Post {i}',
                content=f'Content for post {i}',
                is_approved=True
            )
        response = self.client.get(self.post_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('next', response.data)
        self.assertEqual(len(response.data['results']), 10)  # Default page size

    def test_post_search(self):
        """Test searching for posts."""
        Post.objects.create(
            author=self.user,
            title='Searchable Post',
            content='This post should be found in search.',
            is_approved=True
        )
        response = self.client.get(f"{self.post_url}?search=Searchable")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Searchable Post')

    def test_post_preview_list(self):
        cache.clear()
        """Test retrieving the post preview list."""
        response = self.client.get(self.post_preview_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  
        self.assertIn('author', response.data['results'][0])
        self.assertIn('image_url', response.data['results'][0])

    def test_update_post_stats_not_found(self):
        """Update post stats for a non-existent post."""
        from .tasks import update_post_stats
        non_existent_id = 9999
        update_post_stats(non_existent_id)
        self.assertTrue(True)

    def test_update_post(self):
        """Update a post as the owner."""
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Updated First Post'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated First Post')
        self.assertFalse(self.post1.is_approved)
        self.assertEqual(response.data['message'], "Your post has been updated and is pending approval.")

    def test_update_post_as_staff(self):
        """Update a post as a staff user."""
        self.client.force_authenticate(user=self.staff_user)
        data = {'title': 'Staff Updated First Post'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Staff Updated First Post')
        self.assertTrue(self.post1.is_approved)
        self.assertEqual(response.data['message'], "Your post has been updated successfully.")

    def test_retrieve_unapproved_post_as_non_owner(self):
        """Retrieve an unapproved post as a non-owner."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.post_detail_url(self.post2.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_unapproved_post_as_owner(self):
        """Retrieve an unapproved post as the owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.post_detail_url(self.post2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], self.post2.title)

    def test_retrieve_unapproved_post_as_staff(self):
        """Retrieve an unapproved post as a staff user."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.post_detail_url(self.post2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], self.post2.title)

    def test_search_unapproved_post(self):
        """Ensure unapproved posts are not returned in search results for non-owners."""
        Post.objects.create(
            author=self.user,
            title='Unapproved Searchable Post',
            content='This post should not be found in search.',
            is_approved=False
            )
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"{self.post_url}?search=Unapproved")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.post_url}?search=Unapproved")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Unapproved Searchable Post')

    def test_rating_updates_profile_popularity(self):
        """Ensure rating a post updates the author's profile popularity score."""
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post1.id, 'value': 5}
        response = self.client.post(reverse('create-update-rating'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post1.update_rating_stats()                
        self.user.profile.update_popularity_score()
        self.user.profile.refresh_from_db()
        self.assertGreater(self.user.profile.popularity_score, 0)


    def test_comment_on_post(self):
        """Comment on a post."""
        from comments.models import Comment
        self.client.force_authenticate(user=self.other_user)
        data = {'content': 'Great post!'}
        response = self.client.post(reverse('comment-list', kwargs={'post_id': self.post1.id}), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.author, self.other_user)
        self.assertEqual(comment.post, self.post1)

    def test_tag_user_in_post(self):
        """Tag a user in a post."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Post with Tag',
            'content': 'Content with tag.',
            'tags': [self.other_user.profile_name]
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title='Post with Tag')
        self.assertEqual(new_post.tags.count(), 1)
        tag = new_post.tags.first()
        self.assertEqual(tag.tagged_user, self.other_user)

    def test_post_rating_updates_average(self):
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post1.id, 'value': 4}
        response = self.client.post(reverse('create-update-rating'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.average_rating, 4.0)
        

    def test_follow_user_updates_follower_count(self):
        """Ensure following a user updates follower counts and popularity score."""
        self.client.force_authenticate(user=self.other_user)
        data = {'followed': self.user.id}
        response = self.client.post(reverse('follow-unfollow'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.follower_count, 1)
        self.assertGreater(self.user.profile.popularity_score, 0)

    def test_post_approval_flow(self):
        """Test the approval and disapproval flow of posts."""
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Unapproved Post', 'content': 'Awaiting approval.'}
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title='Unapproved Post')
        self.assertFalse(new_post.is_approved)

        self.client.force_authenticate(user=self.staff_user)
        approve_url = reverse('approve-post', kwargs={'pk': new_post.id})
        response = self.client.patch(approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_post.refresh_from_db()
        self.assertTrue(new_post.is_approved)

        self.client.force_authenticate(user=self.user)
        update_data = {'content': 'Updated content.'}
        response = self.client.patch(self.post_detail_url(new_post.id), update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_post.refresh_from_db()
        self.assertFalse(new_post.is_approved)

    def test_post_list_caching(self):
        cache.clear()
        response1 = self.client.get(self.post_url)
        response2 = self.client.get(self.post_url)
        self.assertEqual(response1.data, response2.data)
    
    def test_tag_nonexistent_user_in_post(self):
            """Test tagging a non-existent user in a post."""
            self.client.force_authenticate(user=self.user)
            data = {
                'title': 'Post with Invalid Tag',
                'content': 'Content with invalid tag.',
                'tags': ['nonexistentuser']
            }
            response = self.client.post(self.post_url, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('tags', response.data['errors'])
            error_message = str(response.data['errors']['tags'][0])
            self.assertIn("User with profile name 'nonexistentuser' does not exist.", error_message)
        
    def test_post_list_filtering(self):
        cache.clear()
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f"{self.post_url}?is_approved=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(f"{self.post_url}?is_approved=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_post_list_ordering(self):
        """Test ordering posts by created_at and updated_at."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f"{self.post_url}?ordering=-created_at")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'Second Post')

        response = self.client.get(f"{self.post_url}?ordering=created_at")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'First Post')

    
    def test_post_creation_with_image(self):
        """Create a post with an image."""
        self.client.force_authenticate(user=self.user)
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        image_file = SimpleUploadedFile(
            'test_image.gif', image_content, content_type='image/gif'
            )
        data = {
            'title': 'Post with Image',
            'content': 'This post has an image.',
            'image': image_file
            }
        response = self.client.post(self.post_url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Post.objects.get(title='Post with Image').image)

    def test_post_update_with_invalid_image(self):
            """Update a post with an invalid image format."""
            self.client.force_authenticate(user=self.user)
            invalid_file = SimpleUploadedFile(
                'invalid.txt', b'not an image', content_type='text/plain'
            )
            data = {'image': invalid_file}
            response = self.client.patch(self.post_detail_url(self.post1.id), data, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('image', response.data['errors'])
            self.assertIn('Upload a valid image.', str(response.data['errors']['image']))
    
    @patch('posts.tasks.update_post_stats.delay')
    def test_post_rating_triggers_update_task(self, mock_update_task):
        self.client.force_authenticate(user=self.other_user)
        data = {'post': self.post1.id, 'value': 4}
        response = self.client.post(reverse('create-update-rating'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_update_task.assert_called_once_with(self.post1.id)

    def test_post_disapproval_sends_email(self):
        """Test that disapproving a post sends an email to the author."""
        self.client.force_authenticate(user=self.staff_user)
        data = {'reason': 'Inappropriate content'}
        response = self.client.post(reverse('disapprove-post', kwargs={'pk': self.post1.id}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your post has been disapproved")
        self.assertIn("Inappropriate content", mail.outbox[0].body)

    def test_post_list_caching(self):
        """Test that post list is cached and returns the same data on subsequent requests."""
        self.client.force_authenticate(user=self.user)
        response1 = self.client.get(self.post_url)
        response2 = self.client.get(self.post_url)
        self.assertEqual(response1.data, response2.data)

    def test_post_search_case_insensitive(self):
        """Test that post search is case-insensitive."""
        Post.objects.create(
            author=self.user,
            title='Case Insensitive Search Test',
            content='This is a test for case-insensitive search.',
            is_approved=True
        )
        response = self.client.get(f"{self.post_url}?search=CASE INSENSITIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Case Insensitive Search Test')

    def test_post_preview_pagination(self):
        """Test pagination of post previews."""
        for i in range(15):
            Post.objects.create(
                author=self.user,
                title=f'Preview Post {i}',
                content=f'Content for preview post {i}',
                is_approved=True
            )
        response = self.client.get(self.post_preview_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertIsNotNone(response.data['next'])

    def test_post_update_resets_approval(self):
        """Test that updating a post resets its approval status."""
        self.client.force_authenticate(user=self.user)
        data = {'content': 'Updated content'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)

    def test_staff_update_preserves_approval(self):
        """Test that staff updates don't reset approval status."""
        self.client.force_authenticate(user=self.staff_user)
        data = {'content': 'Staff updated content'}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertTrue(self.post1.is_approved)

    def test_post_creation_with_invalid_tags(self):
        """Test creating a post with invalid tags."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Post with Invalid Tags',
            'content': 'This post has invalid tags.',
            'tags': ['nonexistent_user', self.other_user.profile_name]
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tags', response.data['errors'])

    def test_post_detail_includes_comments(self):
            """Test that post detail includes associated comments."""
            self.client.force_authenticate(user=self.user)
            Comment.objects.create(post=self.post1, author=self.other_user, content="Test comment")
            response = self.client.get(self.post_detail_url(self.post1.id))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['data']['comments']), 1)
            self.assertEqual(response.data['data']['comments'][0]['content'], "Test comment")

    def test_post_list_performance(self):
            """Test the performance of post list retrieval."""
            for i in range(100):
                Post.objects.create(
                    author=self.user,
                    title=f'Performance Test Post {i}',
                    content=f'Content for performance test post {i}',
                    is_approved=True
                )
            self.client.force_authenticate(user=self.user)
            import time
            start_time = time.time()
            response = self.client.get(self.post_url)
            end_time = time.time()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertLess(end_time - start_time, 1.0)

    def test_explain_query(self):
            """Test the explain_query method for coverage."""            
            Post.explain_query()            
            self.assertTrue(True) 

    def test_create_post_with_duplicate_title(self):
        """Test creating a post with a duplicate title."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'First Post',
            'content': 'Trying to create a post with a duplicate title.'
            }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_message = "A post with this title already exists."
        self.assertEqual(str(response.data['errors']['title'][0]), expected_message)



    def test_update_post_remove_all_tags(self):
        """Test updating a post to remove all tags."""
        self.client.force_authenticate(user=self.user)
        # First, create a post with tags
        data = {
            'title': 'Tagged Post',
            'content': 'Content for the tagged post.',
            'tags': [self.other_user.profile_name]
            }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title='Tagged Post')
        self.assertEqual(new_post.tags.count(), 1)
        update_data = {'tags': []}
        
        response = self.client.patch(self.post_detail_url(new_post.id), update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_post.refresh_from_db()
        self.assertEqual(new_post.tags.count(), 0)

    def test_create_post_unexpected_exception(self):
            """Test handling of unexpected exception during post creation."""
            self.client.force_authenticate(user=self.user)
            data = {
                'title': 'New Post',
                'content': 'Content for the new post.'
            }
            with patch('posts.serializers.PostSerializer.is_valid', side_effect=Exception('Test exception')):
                response = self.client.post(self.post_url, data)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data['message'], "An unexpected error occurred.")
            self.assertIn('Test exception', response.data['errors']['detail'])
            
    def test_update_post_validation_error(self):
        """Test handling of validation error during post update."""
        self.client.force_authenticate(user=self.user)
        data = {'title': ''}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_message = "Failed to update the post. Please check your permissions or provided data."
        self.assertEqual(response.data['message'], expected_message)


        


    def test_create_post_unexpected_exception(self):
        """Test handling of unexpected exception during post creation."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Post',
            'content': 'Content for the new post.'
            }
        with patch('posts.serializers.PostSerializer.is_valid', side_effect=Exception('Test exception')):
            response = self.client.post(self.post_url, data)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data['message'], "An unexpected error occurred.")
            self.assertIn('Test exception', response.data['errors']['detail'])
            
    def test_update_post_stats_success(self):
        """Test that update_post_stats task updates post stats successfully."""
        from posts.tasks import update_post_stats
        # Ensure the post has some ratings
        self.post1.ratings.create(user=self.other_user, value=5)
        update_post_stats(self.post1.id)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.average_rating, 5.0)
        
    
    def test_update_post_stats_post_does_not_exist(self):
        """Test update_post_stats task when post does not exist."""
        from posts.tasks import update_post_stats
        non_existent_id = 9999  
        with self.assertLogs('posts.tasks', level='ERROR') as cm:
            update_post_stats(non_existent_id)
        self.assertIn(f"Post {non_existent_id} not found", cm.output[0])
            
    def test_update_post_stats_unexpected_exception(self):
        """Test update_post_stats task handles unexpected exceptions."""
        from posts.tasks import update_post_stats
        with patch('posts.models.Post.update_rating_stats', side_effect=Exception('Test exception')):
            with self.assertLogs('posts.tasks', level='ERROR') as cm:
                update_post_stats(self.post1.id)
                self.assertIn("Unexpected error in update_post_stats: Test exception", cm.output[0])
                
    @patch('posts.models.Post.update_rating_stats', side_effect=Exception('Test exception'))
    def test_update_post_stats_unexpected_exception(self, mock_method):
        """Test update_post_stats task handles unexpected exceptions."""
        from posts.tasks import update_post_stats
        with self.assertLogs('posts.tasks', level='ERROR') as cm:
            update_post_stats(self.post1.id)
            self.assertIn("Unexpected error in update_post_stats: Test exception", cm.output[0])


class TasksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            profile_name='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Test Content',
            is_approved=True
        )

    def test_update_post_stats_success(self):
        """Test that update_post_stats task updates post stats successfully."""
        # Simulate a rating
        self.post.ratings.create(user=self.user, value=5)
        # Call the task
        update_post_stats(self.post.id)
        # Refresh from database
        self.post.refresh_from_db()
        # Assert that average_rating is updated
        self.assertEqual(self.post.average_rating, 5.0)