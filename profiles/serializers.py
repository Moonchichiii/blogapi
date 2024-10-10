from rest_framework import serializers
from .models import Profile
from django.db.models import Avg

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the Profile model."""
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user_id', 'profile_name', 'bio', 'image', 'follower_count',
            'following_count', 'popularity_score', 'is_following', 'comment_count', 'tag_count'
        ]
        read_only_fields = [
            'id', 'user_id', 'profile_name', 'follower_count',
            'following_count', 'popularity_score', 'comment_count', 'tag_count'
        ]

    def get_is_following(self, obj):
        """Check if the current user is following the profile."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.user.followers.filter(follower=user).exists()
        return False

    def to_representation(self, instance: Profile) -> dict:
        """Customize the representation of the instance."""
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def update(self, instance: Profile, validated_data: dict) -> Profile:
        """Update the profile instance with validated data."""
        instance.bio = validated_data.get('bio', instance.bio)
        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()
        return instance


class PopularFollowerSerializer(serializers.ModelSerializer):
    """Serializer for popular followers."""
    profile_name = serializers.CharField(source='user.profile_name')
    average_rating = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['profile_name', 'image', 'average_rating', 'comment_count', 'post_count', 'popularity_score', 'tags']

    def get_average_rating(self, obj):
        """Get the average rating of the user's posts."""
        return obj.user.posts.aggregate(Avg('average_rating'))['average_rating__avg'] or 0

    def get_post_count(self, obj):
        """Get the count of the user's posts."""
        return obj.user.posts.count()

    def get_tags(self, obj):
        return obj.user.tags.values_list('tagged_user__profile_name', flat=True)

