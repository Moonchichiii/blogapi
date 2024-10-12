from rest_framework import serializers
from django.db.models import Avg
from .models import Profile
from posts.serializers import PostSerializer

class ProfileSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    bio = serializers.CharField(required=False, max_length=500)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    posts = PostSerializer(many=True, read_only=True, source='user.posts')
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user_id', 'profile_name', 'bio', 'image', 'follower_count',
            'following_count', 'popularity_score', 'is_following', 'posts'
        ]
        read_only_fields = [
            'id', 'user_id', 'profile_name', 'follower_count', 'following_count', 'popularity_score'
        ]

    def get_is_following(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.user.followers.filter(follower=user).exists()
        return False

    def to_representation(self, instance: Profile) -> dict:
        """Customize instance representation."""
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def update(self, instance: Profile, validated_data: dict) -> Profile:
        """Update profile instance."""
        instance.bio = validated_data.get('bio', instance.bio)
        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()
        return instance

class PopularFollowerSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name')
    average_rating = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'profile_name', 'image', 'average_rating', 'comment_count',
            'post_count', 'popularity_score', 'tags'
        ]

    def get_average_rating(self, obj):
        """Get average rating of user's posts."""
        return obj.user.posts.aggregate(Avg('average_rating'))['average_rating__avg'] or 0

    def get_post_count(self, obj):
        """Get count of user's posts."""
        return obj.user.posts.count()

    def get_tags(self, obj):
        """Get tags of user's posts."""
        return obj.user.tags.values_list('tagged_user__profile_name', flat=True)
