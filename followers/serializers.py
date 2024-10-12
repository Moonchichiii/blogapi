from rest_framework import serializers
from profiles.serializers import ProfileSerializer
from .models import Follow

class FollowSerializer(serializers.ModelSerializer):
    """Serializer for Follow model with profile details."""
    follower_profile = serializers.SerializerMethodField()
    followed_profile = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_profile', 'followed', 'followed_profile', 'created_at']
        read_only_fields = ['follower']

    def get_follower_profile(self, obj):
        """Get profile data of the follower."""
        return ProfileSerializer(obj.follower.profile).data

    def get_followed_profile(self, obj):
        """Get profile data of the followed."""
        return ProfileSerializer(obj.followed.profile).data
