from django.contrib.auth import get_user_model
from django.test import TestCase
from django.db.utils import IntegrityError
from unittest.mock import patch
from popularity.models import PopularityMetrics
from posts.models import Post
from profiles.models import Profile
from followers.models import Follow
from popularity.tasks import aggregate_popularity_score

User = get_user_model()

class PopularityMetricsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            profile_name="Test User"
        )
        self.metrics, _ = PopularityMetrics.objects.get_or_create(user=self.user)

    def test_popularity_metrics_creation(self):
        self.assertEqual(self.metrics.user, self.user)
        self.assertEqual(self.metrics.follower_count, 0)
        self.assertEqual(self.metrics.average_post_rating, 0.0)
        self.assertEqual(self.metrics.post_count, 0)
        self.assertEqual(self.metrics.popularity_score, 0.0)

    def test_popularity_metrics_str_method(self):
        self.assertEqual(str(self.metrics), f"Popularity Metrics for {self.user.profile_name}")

    def test_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            PopularityMetrics.objects.create(user=self.user)

class AggregatePopularityScoreTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            profile_name="Test User"
        )
        self.profile = Profile.objects.get(user=self.user)
        self.metrics, _ = PopularityMetrics.objects.get_or_create(user=self.user)

    def test_aggregate_popularity_score_no_posts_no_followers(self):
        result = aggregate_popularity_score(self.user.id)
        self.metrics.refresh_from_db()
        
        self.assertEqual(self.metrics.post_count, 0)
        self.assertEqual(self.metrics.average_post_rating, 0)
        self.assertEqual(self.metrics.follower_count, 0)
        self.assertEqual(self.metrics.popularity_score, 0)
        self.assertEqual(result, f"Updated popularity score for user {self.user.id}")

    def test_aggregate_popularity_score_with_posts_and_followers(self):
        Post.objects.create(author=self.user, content="Test post", average_rating=4.5)
        self.profile.follower_count = 10
        self.profile.save()

        result = aggregate_popularity_score(self.user.id)
        self.metrics.refresh_from_db()

        self.assertEqual(self.metrics.post_count, 1)
        self.assertEqual(self.metrics.average_post_rating, 4.5)
        self.assertEqual(self.metrics.follower_count, 10)
        expected_score = (4.5 * 0.6) + (1 * 0.3) + (10 * 0.1)
        self.assertAlmostEqual(self.metrics.popularity_score, expected_score, places=2)
        self.assertEqual(result, f"Updated popularity score for user {self.user.id}")

    def test_aggregate_popularity_score_no_profile(self):
        self.profile.delete()
        result = aggregate_popularity_score(self.user.id)
        self.assertIn("Error: Profile not found for user", result)

    @patch('popularity.tasks.Post.objects.filter')
    def test_aggregate_popularity_score_database_error(self, mock_post_filter):
        mock_post_filter.side_effect = Exception("Database error")
        result = aggregate_popularity_score(self.user.id)
        self.assertIn("Error updating popularity score for user", result)

    def test_logging(self):
        with self.assertLogs('popularity.tasks', level='INFO') as cm:
            aggregate_popularity_score(self.user.id)
        self.assertTrue(any("Calculated popularity score for user" in msg for msg in cm.output))
        self.assertTrue(any(f"Post count for user {self.user.id}:" in msg for msg in cm.output))
        
        self.assertEqual(self.metrics.post_count, 1)
        self.assertEqual(self.metrics.average_post_rating, 0)
        expected_score = (0 * 0.6) + (1 * 0.3) + (0 * 0.1)
        self.assertAlmostEqual(self.metrics.popularity_score, expected_score, places=2)

    def test_aggregate_popularity_score_updates_existing_metrics(self):
        self.metrics.post_count = 5
        self.metrics.average_post_rating = 2.0
        self.metrics.follower_count = 10
        self.metrics.popularity_score = 100
        self.metrics.save()

        Post.objects.create(author=self.user, content="New post", average_rating=5.0)
        
        result = aggregate_popularity_score(self.user.id)
        self.metrics.refresh_from_db()

        self.assertEqual(self.metrics.post_count, 1)
        self.assertEqual(self.metrics.average_post_rating, 5.0)
        self.assertEqual(self.metrics.follower_count, 0)
        expected_score = (5.0 * 0.6) + (1 * 0.3) + (0 * 0.1)
        self.assertAlmostEqual(self.metrics.popularity_score, expected_score, places=2)

    @patch('popularity.tasks.logger.info')
    def test_logging(self):
        with self.assertLogs('popularity.tasks', level='INFO') as cm:
            aggregate_popularity_score(self.user.id)
            self.assertTrue(any("Calculated popularity score for user" in msg for msg in cm.output))
            self.assertTrue(any(f"Post count for user {self.user.id}:" in msg for msg in cm.output))

class PopularityMetricsQueryTests(TestCase):
    def setUp(self):
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f"user{i}@example.com", 
                password="pass123", 
                profile_name=f"User {i}"
            )
            self.users.append(user)
            profile, _ = Profile.objects.get_or_create(user=user)
            metrics, _ = PopularityMetrics.objects.get_or_create(user=user)
            metrics.popularity_score = i * 10
            metrics.save()

    def test_order_by_popularity_score(self):
        ordered_metrics = PopularityMetrics.objects.order_by('-popularity_score')
        self.assertEqual(list(ordered_metrics.values_list('user__id', flat=True)), [5, 4, 3, 2, 1])

    def test_filter_by_popularity_score(self):
        high_popularity = PopularityMetrics.objects.filter(popularity_score__gte=20)
        self.assertEqual(high_popularity.count(), 3)

    def test_aggregate_functions(self):
        from django.db.models import Avg, Max, Min
        
        avg_score = PopularityMetrics.objects.aggregate(Avg('popularity_score'))['popularity_score__avg']
        max_score = PopularityMetrics.objects.aggregate(Max('popularity_score'))['popularity_score__max']
        min_score = PopularityMetrics.objects.aggregate(Min('popularity_score'))['popularity_score__min']
        
        self.assertEqual(avg_score, 20)
        self.assertEqual(max_score, 40)
        self.assertEqual(min_score, 0)