from rest_framework import serializers
from .models import Comment
from tags.serializers import ProfileTagSerializer

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.profile_name', read_only=True)
    tags = ProfileTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_name', 'content', 'created_at', 'updated_at', 'is_approved']
        read_only_fields = ['id', 'author', 'author_name', 'created_at', 'updated_at', 'is_approved','tags']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)