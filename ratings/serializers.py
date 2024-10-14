from rest_framework import serializers
from posts.models import Post
from .models import Rating
from .messages import STANDARD_MESSAGES


class RatingSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source="user.profile_name", read_only=True)
    post_title = serializers.CharField(source="post.title", read_only=True)
    post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.filter(is_approved=True)
    )

    class Meta:
        model = Rating
        fields = ["id", "profile_name", "post", "value", "post_title"]

    def validate_value(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError(
                STANDARD_MESSAGES["INVALID_RATING_VALUE"]["message"]
            )
        return value
