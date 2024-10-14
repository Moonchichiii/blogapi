import logging

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.models import CustomUser
from tags.models import ProfileTag
from .models import Post

logger = logging.getLogger(__name__)


class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing posts with author and ownership information.
    """

    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "title", "content", "author", "created_at", "is_owner"]

    def get_is_owner(self, obj):
        """
        Check if the current user is the owner of the post.
        """
        request = self.context.get("request", None)
        is_owner = (
            request.user == obj.author
            if request and request.user.is_authenticated
            else False
        )
        logger.debug(f"Checking ownership for post {obj.id}: {is_owner}")
        return is_owner


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating posts with tags and image validation.
    """

    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tagged_users = serializers.SerializerMethodField(read_only=True)
    tags = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "image",
            "author",
            "created_at",
            "average_rating",
            "is_owner",
            "tagged_users",
            "tags",
        ]
        read_only_fields = ["id", "author", "created_at", "average_rating"]

    def get_is_owner(self, obj):
        """
        Check if the current user is the owner of the post.
        """
        request = self.context.get("request", None)
        return (
            request.user == obj.author
            if request and request.user.is_authenticated
            else False
        )

    def get_tagged_users(self, obj):
        """
        Get the list of tagged users' profile names.
        """
        return [tag.tagged_user.profile_name for tag in obj.tags.all()]

    def validate_title(self, value):
        """
        Validate that the post title is unique.
        """
        logger.debug(f"Validating title: {value}")
        if Post.objects.filter(title=value).exists():
            logger.error(f"Duplicate title detected: {value}")
            raise ValidationError("A post with this title already exists.")
        return value

    def create(self, validated_data):
        """
        Create a new post and handle tags.
        """
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        self._handle_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        """
        Update an existing post and handle tags.
        """
        tags_data = validated_data.pop("tags", [])
        instance = super().update(instance, validated_data)
        self._handle_tags(instance, tags_data)
        return instance

    def _handle_tags(self, post, tags_data):
        """
        Handle the creation and association of tags with the post.
        """
        tag_objects = []
        for tag_name in tags_data:
            tagged_user = CustomUser.objects.filter(profile_name=tag_name).first()
            if not tagged_user:
                raise ValidationError({"tags": f"User '{tag_name}' does not exist."})
            tag, created = ProfileTag.objects.get_or_create(
                tagged_user=tagged_user,
                tagger=post.author,
                content_type=ContentType.objects.get_for_model(Post),
                object_id=post.id,
            )
            tag_objects.append(tag)
        post.tags.set(tag_objects)

    def validate_image(self, value):
        """
        Validate the uploaded image for format and size.
        """
        if value and not value.name.lower().endswith(
            ("jpg", "jpeg", "png", "gif", "webp")
        ):
            raise serializers.ValidationError("Upload a valid image.")
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Image must be less than 2MB.")
        return value


class LimitedPostSerializer(serializers.ModelSerializer):
    """
    Serializer for limited post information with image URL.
    """

    author = serializers.CharField(source="author.profile_name", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "title", "author", "image_url"]

    def get_image_url(self, obj):
        """
        Get the URL of the post's image.
        """
        image_url = obj.image.url if obj.image and hasattr(obj.image, "url") else None
        logger.debug(f"Image URL for post {obj.id}: {image_url}")
        return image_url
