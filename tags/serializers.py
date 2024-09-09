from rest_framework import serializers
from .models import ProfileTag

class ProfileTagSerializer(serializers.ModelSerializer):
    tagger_name = serializers.CharField(source='tagger.profile_name', read_only=True)
    tagged_user_name = serializers.CharField(source='tagged_user.profile_name', read_only=True)

    class Meta:
        model = ProfileTag
        fields = ['id', 'tagged_user', 'tagged_user_name', 'tagger', 'tagger_name', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['tagger', 'content_type', 'object_id']
