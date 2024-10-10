"""
Serializers for the followers app.
"""

from rest_framework import serializers
from profiles.serializers import ProfileSerializer
from .models import Follow

class FollowSerializer(serializers.ModelSerializer):
    follower_profile = serializers.SerializerMethodField()
    followed_profile = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = [
            'id', 'follower', 'follower_name', 'followed', 'followed_name',
            'follower_profile', 'followed_profile', 'created_at'
        ]
        read_only_fields = ['follower']

    def get_follower_profile(self, obj):
        return ProfileSerializer(obj.follower.profile).data

    def get_followed_profile(self, obj):
        return ProfileSerializer(obj.followed.profile).data