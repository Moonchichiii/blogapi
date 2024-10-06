from rest_framework import serializers
from posts.models import Post
from .models import Rating
from .messages import STANDARD_MESSAGES

class RatingSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Rating
        fields = ['id', 'user', 'profile_name', 'post', 'post_title', 'value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'profile_name', 'created_at', 'updated_at']

    def validate_value(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError(STANDARD_MESSAGES['INVALID_RATING_VALUE']['message'])
        return value

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(STANDARD_MESSAGES['POST_NOT_FOUND']['message'])
        return value