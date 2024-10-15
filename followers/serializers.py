from rest_framework import serializers
from django.db.models import Avg
from .models import Follow
from posts.models import Post

class FollowSerializer(serializers.ModelSerializer):
    """Serializer for the Follow model with additional fields for profile details and post statistics."""
    
    profile_name = serializers.CharField(source="follower.profile.profile_name", read_only=True)
    popularity_score = serializers.FloatField(source="follower.profile.popularity_score", read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)
    post_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ["id", "follower", "followed", "created_at", "profile_name", "popularity_score", "average_rating", "post_count"]
        read_only_fields = ["follower", "created_at", "profile_name", "popularity_score", "average_rating", "post_count"]

    def get_average_rating(self, obj):
        """Calculate the average rating of posts by the follower."""
        return Post.objects.filter(author=obj.follower).aggregate(Avg("average_rating"))["average_rating__avg"] or 0

    def get_post_count(self, obj):
        """Count the number of posts by the follower."""
        return Post.objects.filter(author=obj.follower).count()

    def to_representation(self, instance):
        """Customize the representation of the serialized data."""
        representation = super().to_representation(instance)
        if self.context.get('request').query_params.get('order_by') != 'popularity':
            representation.pop('popularity_score', None)
            representation.pop('average_rating', None)
            representation.pop('post_count', None)
        return representation