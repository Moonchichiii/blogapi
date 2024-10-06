from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from comments.models import Comment
from posts.models import Post
from posts.tasks import update_post_stats
from posts.serializers import LimitedPostSerializer, PostListSerializer

User = get_user_model()

class PostTests(APITestCase):
    """Test suite for post-related functionalities."""

    def setUp(self):
        """Set up test data and clear cache."""
        cache.clear()
        self.client = APIClient()

        # Create test users
        self.user = self._create_user('testuser@example.com', 'testuser', 'testpass123')
        self.other_user = self._create_user('otheruser@example.com', 'otheruser', 'otherpass123')
        self.staff_user = self._create_user('staffuser@example.com', 'staffuser', 'staffpass123', is_staff=True)
        self.admin_user = self._create_user(
            'adminuser@example.com', 'adminuser', 'adminpass123', is_staff=True, is_superuser=True
        )

        # Create posts
        now = timezone.now()
        self.post1 = self._create_post(
            self.user, 'First Post', 'Content for the first post.', True, now - timedelta(minutes=2)
        )
        self.post2 = self._create_post(
            self.user, 'Second Post', 'Content for the second post.', False, now - timedelta(minutes=1)
        )

        # Set URLs
        self.post_list_url = reverse('post-list')
        self.post_detail_url = lambda pk: reverse('post-detail', kwargs={'pk': pk})

    def _create_user(self, email, profile_name, password, is_staff=False, is_superuser=False):
        """Helper method to create a user."""
        return User.objects.create_user(email=email, profile_name=profile_name, password=password, is_staff=is_staff, is_superuser=is_superuser)

    def _create_post(self, author, title, content, is_approved=False, created_at=None):
        """Helper method to create a post."""
        post = Post.objects.create(author=author, title=title, content=content, is_approved=is_approved)
        if created_at:
            post.created_at = created_at
            post.save()
        return post

    def _authenticate_user(self, user):
        """Helper method to authenticate a user."""
        self.client.force_authenticate(user=user)

    def _assert_email_sent(self, subject, body_contains):
        """Helper method to assert email content."""
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(body_contains, mail.outbox[0].body)

    def test_post_update_with_invalid_image(self):
        """Test updating a post with an invalid image."""
        self._authenticate_user(self.user)
        invalid_file = SimpleUploadedFile("invalid.txt", b"not an image", content_type="text/plain")
        response = self.client.patch(self.post_detail_url(self.post1.id), {"image": invalid_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Upload a valid image.", str(response.data["errors"]["image"]))

    @patch('posts.tasks.update_post_stats.delay')
    def test_post_rating_triggers_update_task(self, mock_update_task):
        """Test that rating a post triggers the update task."""
        self._authenticate_user(self.other_user)
        response = self.client.post(reverse('create-update-rating'), {'post': self.post1.id, 'value': 4})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_update_task.assert_called_once_with(self.post1.id)

    def test_post_disapproval_sends_email(self):
        """Test that disapproving a post sends an email."""
        self._authenticate_user(self.staff_user)
        response = self.client.post(reverse("disapprove-post", kwargs={"pk": self.post1.id}), {"reason": "Inappropriate content"})
        self._assert_email_sent("Your post has been disapproved", "Inappropriate content")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_search_case_insensitive(self):
        """Test case-insensitive search for posts."""
        self._create_post(self.user, "Case Insensitive Search Test", "Test content", True)
        response = self.client.get(f"{self.post_list_url}?search=CASE INSENSITIVE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "Case Insensitive Search Test")

    def test_post_update_resets_approval(self):
        """Test that updating a post resets its approval status."""
        self._authenticate_user(self.user)
        response = self.client.patch(self.post_detail_url(self.post1.id), {"content": "Updated content"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)

    def test_staff_update_preserves_approval(self):
        """Test that staff updating a post preserves its approval status."""
        self._authenticate_user(self.staff_user)
        response = self.client.patch(self.post_detail_url(self.post1.id), {"content": "Staff updated content"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertTrue(self.post1.is_approved)

    def test_post_creation_with_invalid_tags(self):
        """Test creating a post with invalid tags."""
        self._authenticate_user(self.user)
        response = self.client.post(self.post_list_url, {
            "title": "Post with Invalid Tags",
            "content": "Content with invalid tags",
            "tags": ["nonexistent_user", self.other_user.profile_name]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data["errors"])

    def test_post_detail_includes_comments(self):
        """Test that post detail includes comments."""
        self._authenticate_user(self.user)
        Comment.objects.create(post=self.post1, author=self.other_user, content="Test comment")
        response = self.client.get(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["comments"]), 1)
        self.assertEqual(response.data["data"]["comments"][0]["content"], "Test comment")

    def test_partial_update_post(self):
        """Test partially updating a post."""
        self._authenticate_user(self.user)
        data = {"content": "Partially updated content"}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.content, "Partially updated content")

    def test_retrieve_non_existent_post(self):
        """Test retrieving a non-existent post."""
        self._authenticate_user(self.user)
        response = self.client.get(self.post_detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_post_validation_error(self):
        """Test validation error when updating a post."""
        self._authenticate_user(self.user)
        response = self.client.patch(self.post_detail_url(self.post1.id), {"title": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_post_as_non_owner_non_staff(self):
        """Test that a non-owner non-staff cannot update a post."""
        self._authenticate_user(self.other_user)
        response = self.client.patch(self.post_detail_url(self.post1.id), {"title": "Unauthorized update"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_post_with_tags_and_image(self):
        """Test creating a post with both tags and an image."""
        self.client.force_authenticate(user=self.user)
        image_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        image_file = SimpleUploadedFile("test_image.gif", image_content, content_type="image/gif")
        data = {
            "title": "Post with Tags and Image",
            "content": "This post has tags and an image.",
            "tags": [self.other_user.profile_name],
            "image": image_file,
        }
        response = self.client.post(self.post_list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title="Post with Tags and Image")
        self.assertIsNotNone(new_post.image)
        self.assertEqual(new_post.tags.count(), 1)

    def test_update_post_stats_success(self):
        """Test that update_post_stats task updates post stats successfully."""
        self.post1.ratings.create(user=self.other_user, value=5)
        update_post_stats(self.post1.id)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.average_rating, 5.0)

        # Test with no ratings
        self.post2.update_rating_statistics()
        self.assertEqual(self.post2.average_rating, 0)

    def test_create_post_with_duplicate_title(self):
        """Test creating a post with a duplicate title."""
        self._authenticate_user(self.user)
        data = {
            "title": "First Post",  # duplicate title
            "content": "Trying to create a post with a duplicate title.",
        }
        response = self.client.post(self.post_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_message = "A post with this title already exists."
        self.assertEqual(str(response.data["errors"]["title"][0]), expected_message)

    def test_create_post_with_invalid_image_format(self):
        """Test post creation with an invalid image format."""
        self._authenticate_user(self.user)
        invalid_image = SimpleUploadedFile("test.txt", b"Invalid image data", content_type="text/plain")
        data = {
            "title": "Post with invalid image",
            "content": "Testing invalid image format",
            "image": invalid_image
        }
        response = self.client.post(self.post_list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Upload a valid image", str(response.data["errors"]["image"]))

    def test_post_list_filter_by_approval_status(self):
        """Test filtering posts by approval status."""
        self._authenticate_user(self.user)
        response = self.client.get(f"{self.post_list_url}?is_approved=True")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_post_list_order_by_created_at(self):
        """Test ordering posts by created_at."""
        self._authenticate_user(self.user)
        response = self.client.get(f"{self.post_list_url}?ordering=created_at")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "First Post")

    def test_retrieve_unapproved_post_by_non_owner(self):
        """Test that a non-owner cannot retrieve an unapproved post."""
        self._authenticate_user(self.other_user)
        response = self.client.get(self.post_detail_url(self.post2.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_post_unexpected_exception(self):
        """Test handling of unexpected exception during post creation."""
        self._authenticate_user(self.user)
        data = {"title": "New Post", "content": "Content for the new post."}

        # Simulate unexpected exception
        with patch("posts.serializers.PostSerializer.is_valid", side_effect=Exception("Test exception")):
            response = self.client.post(self.post_list_url, data)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("Test exception", response.data["errors"]["detail"])

    def test_admin_approve_post(self):
        """Test that an admin can approve a post."""
        self._authenticate_user(self.admin_user)
        approve_url = reverse("approve-post", kwargs={"pk": self.post2.id})
        response = self.client.put(approve_url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post2.refresh_from_db()
        self.assertTrue(self.post2.is_approved)

    def test_approve_non_existent_post(self):
        """Test approving a non-existent post."""
        self._authenticate_user(self.admin_user)
        approve_url = reverse("approve-post", kwargs={"pk": 9999})
        response = self.client.put(approve_url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_disapprove_post(self):
        """Test that an admin can disapprove a post."""
        self._authenticate_user(self.admin_user)
        disapprove_url = reverse("disapprove-post", kwargs={"pk": self.post1.id})
        response = self.client.post(disapprove_url, {"reason": "Inappropriate content"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.is_approved)

    def test_disapprove_non_existent_post(self):
        """Test disapproving a non-existent post."""
        self._authenticate_user(self.admin_user)
        disapprove_url = reverse("disapprove-post", kwargs={"pk": 9999})
        response = self.client.post(disapprove_url, {"reason": "Test reason"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('posts.views.PostList.check_throttles', return_value=None)
    @patch("django.core.cache.cache.get")
    def test_post_list_cache_hit(self, mock_cache_get, mock_throttles):
        """Test that the post list view hits the cache."""
        mock_cache_get.return_value = None
        response = self.client.get(self.post_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_cache_get.called)

    def test_post_retrieve_success(self):
        """Test retrieving a post successfully."""
        self._authenticate_user(self.user)
        response = self.client.get(self.post_detail_url(self.post1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], self.post1.title)

    def test_post_list_search(self):
        """Test searching posts by title."""
        self._authenticate_user(self.user)
        response = self.client.get(f"{self.post_list_url}?search=First")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "First Post")

    def test_post_list_ordering(self):
        """Test ordering posts by created_at in descending order."""
        self._authenticate_user(self.user)
        response = self.client.get(f"{self.post_list_url}?ordering=-created_at")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], "Second Post")

    def test_post_update_by_staff(self):
        """Test that a staff member can update a post."""
        self._authenticate_user(self.staff_user)
        data = {"content": "Updated by staff"}
        response = self.client.patch(self.post_detail_url(self.post1.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.content, "Updated by staff")
        self.assertTrue(self.post1.is_approved)

    @patch('posts.models.Post.objects.get')
    def test_update_post_stats_error(self, mock_get):
        """Test error handling in update_post_stats task."""
        mock_get.side_effect = Post.DoesNotExist
        update_post_stats(999)

    def test_create_post_validation_error(self):
        """Test validation error when creating a post."""
        self._authenticate_user(self.user)
        response = self.client.post(self.post_list_url, {"title": "", "content": "Test content"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_post_not_owner(self):
        """Test that a non-owner cannot update a post."""
        self._authenticate_user(self.other_user)
        response = self.client.patch(self.post_detail_url(self.post1.id), {"content": "Updated content"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_explain_query(self):
        """Test the explain_query method."""
        with self.assertLogs('posts.models', level='INFO') as cm:
            Post.explain_query()
            self.assertTrue(any('EXPLAIN' in log for log in cm.output))

    def test_limited_post_serializer(self):
        """Test the LimitedPostSerializer."""
        serializer = LimitedPostSerializer(self.post1)
        data = serializer.data
        self.assertEqual(set(data.keys()), {'id', 'title', 'author', 'image_url'})
        self.assertEqual(data['author'], self.user.profile_name)

    def test_post_preview_list(self):
        """Test the PostPreviewList view."""
        response = self.client.get(reverse('post-previews'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        for post in response.data['results']:
            self.assertIn('id', post)
            self.assertIn('title', post)
            self.assertIn('author', post)
            self.assertIn('image_url', post)
            self.assertNotIn('content', post)

    def test_post_list_serializer(self):
        """Test the PostListSerializer."""
        serializer = PostListSerializer(self.post1)
        data = serializer.data
        self.assertEqual(set(data.keys()), {'id', 'title', 'author', 'created_at', 'average_rating', 'is_owner', 'comment_count', 'tag_count'})
        self.assertEqual(data['author'], self.user.profile_name)