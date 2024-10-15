import logging
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from accounts.models import CustomUser
from tags.models import ProfileTag
from .models import Post
from backend.utils import validate_image

logger = logging.getLogger(__name__)

class PostListSerializer(serializers.ModelSerializer):
    """Serializer for listing posts with minimal fields."""
    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Post
        fields = ["id", "title", "content", "author", "created_at", "is_owner", "image"]

    def get_is_owner(self, obj):
        request = self.context.get("request", None)
        return request.user == obj.author if request and request.user.is_authenticated else False

class PostSerializer(serializers.ModelSerializer):
    """Serializer for creating, updating, and displaying detailed post information."""
    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tagged_users = serializers.SerializerMethodField(read_only=True)
    tags = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Post
        fields = [
            "id", "title", "content", "image", "author",
            "created_at", "average_rating", "is_owner", "tagged_users", "tags"
        ]
        read_only_fields = ["id", "author", "created_at", "average_rating"]

    def get_is_owner(self, obj):
        request = self.context.get("request", None)
        return request.user == obj.author if request and request.user.is_authenticated else False

    def get_tagged_users(self, obj):
        return [tag.tagged_user.profile_name for tag in obj.tags.all()]

    def validate_image(self, value):
        return validate_image(value)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request", None)
        if not request.user.is_authenticated:
            return {
                "id": representation["id"],
                "title": representation["title"],
                "author": representation["author"],
                "image": representation.get("image"),
            }
        return representation

    def validate_title(self, value):
        if Post.objects.filter(title=value).exists():
            raise ValidationError("A post with this title already exists.")
        return value

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        self._handle_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", [])
        instance = super().update(instance, validated_data)
        self._handle_tags(instance, tags_data)
        return instance

    def _handle_tags(self, post, tags_data):
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