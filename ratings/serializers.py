from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from posts.models import Post
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source="user.profile_name", read_only=True)
    post_title = serializers.CharField(source="post.title", read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    value = serializers.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating value must be between 1 and 5."),
            MaxValueValidator(5, message="Rating value must be between 1 and 5.")
        ]
    )

    class Meta:
        model = Rating
        fields = ["id", "profile_name", "post", "value", "post_title"]

    def validate_value(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating value must be between 1 and 5.")
        return value

    def validate_post(self, value):
        if not value.is_approved:
            raise serializers.ValidationError("You cannot rate an unapproved post.")
        return value

    def validate(self, attrs):
        if attrs['post'].author == self.context['request'].user:
            raise serializers.ValidationError("You cannot rate your own post.")
        return attrs