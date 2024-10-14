from rest_framework import serializers
from .models import Follow
from rest_framework import serializers
from profiles.models import Profile
from django.db.models import Avg
from posts.models import Post


class FollowSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(
        source="follower.profile.profile_name", default=""
    )

    class Meta:
        model = Follow
        fields = ["id", "follower", "followed", "created_at", "profile_name"]
        read_only_fields = ["follower", "created_at"]


class PopularFollowerSerializer(serializers.ModelSerializer):
    """Serializer for popular followers, including profile details and post statistics."""

    profile_name = serializers.CharField(
        source="follower.profile.profile_name", default=""
    )
    popularity_score = serializers.FloatField(
        source="follower.profile.popularity_score", default=0
    )
    average_rating = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ["profile_name", "popularity_score", "average_rating", "post_count"]
        read_only_fields = ["follower", "created_at"]

    def get_average_rating(self, obj):
        """Get the average rating of the follower's posts."""
        return (
            Post.objects.filter(author=obj.follower).aggregate(Avg("average_rating"))[
                "average_rating__avg"
            ]
            or 0
        )

    def get_post_count(self, obj):
        """Get the count of posts created by the follower."""
        return Post.objects.filter(author=obj.follower).count()
