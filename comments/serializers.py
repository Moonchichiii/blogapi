from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.profile_name', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'author_name', 'created_at', 'updated_at']
        extra_kwargs = {'post': {'required': False, 'write_only': True}}

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and not request.user.is_authenticated:
            representation.pop('content', None)
        return representation