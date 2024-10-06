"""
Serializers for the comments app.
"""

from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    """
    author = serializers.CharField(source='author.profile_name', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'content', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'post': {'required': False, 'write_only': True}
        }

    def to_representation(self, instance):
        """
        Customize the representation of the Comment instance.
        Remove 'content' field if the user is not authenticated.
        """
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and not request.user.is_authenticated:
            representation.pop('content', None)
        return representation
