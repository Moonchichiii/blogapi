from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    """
    author = serializers.CharField(source='author.profile_name', read_only=True)
    author_image = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_image', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author_image(self, obj):
        """
        Get the URL of the author's profile image.
        """
        return obj.author.profile.image.url if obj.author.profile.image else None

    def to_representation(self, instance):
        """
        Customize the representation of the Comment instance.
        """
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and not request.user.is_authenticated:
            representation.pop('content', None)
        return representation
