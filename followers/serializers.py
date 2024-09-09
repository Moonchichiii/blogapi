from rest_framework import serializers
from .models import Follow

class FollowSerializer(serializers.ModelSerializer):
    follower_name = serializers.CharField(source='follower.profile_name', read_only=True)
    followed_name = serializers.CharField(source='followed.profile_name', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_name', 'followed', 'followed_name', 'created_at']
        read_only_fields = ['follower']