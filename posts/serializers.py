from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Post
from backend.utils import validate_image

class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for post listings."""

    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model: type = Post
        fields: list = [
            "id", 
            "title", 
            "content", 
            "author", 
            "created_at", 
            "is_owner", 
            "image",
            "average_rating",
            "total_ratings"
        ]
        read_only_fields: list = ["id", "author", "created_at", "average_rating", "total_ratings"]

    def get_is_owner(self, obj: Post) -> bool:
        """
        Determine if the current user is the owner of the post.

        Args:
            obj (Post): The post instance.

        Returns:
            bool: True if the user is the owner, False otherwise.
        """
        request = self.context.get("request")
        return request and request.user.is_authenticated and request.user == obj.author

class PostSerializer(serializers.ModelSerializer):
    """Detailed serializer for single post view."""

    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    ratings_count = serializers.IntegerField(source='ratings.count', read_only=True)

    class Meta:
        model: type = Post
        fields: list = [
            "id",
            "title",
            "content",
            "image",
            "author",
            "created_at",
            "updated_at",
            "average_rating",
            "total_ratings",
            "is_owner",
            "comments_count",
            "ratings_count",
            "is_approved"
        ]
        read_only_fields: list = [
            "id", 
            "author", 
            "created_at", 
            "updated_at", 
            "average_rating", 
            "total_ratings"
        ]

    def get_is_owner(self, obj: Post) -> bool:
        """
        Determine if the current user is the owner of the post.

        Args:
            obj (Post): The post instance.

        Returns:
            bool: True if the user is the owner, False otherwise.
        """
        request = self.context.get("request")
        return request and request.user.is_authenticated and request.user == obj.author

    def validate_image(self, value: str) -> str:
        """
        Validate the image field.

        Args:
            value (str): The image value.

        Returns:
            str: The validated image value.
        """
        return validate_image(value)

    def validate_title(self, value: str) -> str:
        """
        Ensure title uniqueness with case-insensitive comparison.

        Args:
            value (str): The title value.

        Raises:
            ValidationError: If a post with the same title already exists.

        Returns:
            str: The validated title value.
        """
        if Post.objects.filter(title__iexact=value).exists():
            raise ValidationError("A post with this title already exists.")
        return value