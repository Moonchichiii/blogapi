from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from posts.models import Post
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model."""

    profile_name: serializers.CharField = serializers.CharField(source="user.profile_name", read_only=True)
    post_title: serializers.CharField = serializers.CharField(source="post.title", read_only=True)
    post: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    value: serializers.IntegerField = serializers.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating value must be between 1 and 5."),
            MaxValueValidator(5, message="Rating value must be between 1 and 5.")
        ]
    )

    class Meta:
        """Meta class for RatingSerializer."""
        model = Rating
        fields = ["id", "profile_name", "post", "value", "post_title"]
        read_only_fields = ["id", "profile_name", "post_title"]

    def validate(self, attrs: dict) -> dict:
        """
        Validate the Rating instance.

        Args:
            attrs (dict): Attributes to validate.

        Returns:
            dict: Validated attributes.

        Raises:
            serializers.ValidationError: If the post is not approved or if the user is rating their own post.
        """
        if not attrs['post'].is_approved:
            raise serializers.ValidationError("You cannot rate an unapproved post.")
        if attrs['post'].author == self.context['request'].user:
            raise serializers.ValidationError("You cannot rate your own post.")
        return attrs