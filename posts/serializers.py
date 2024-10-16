from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser
from tags.models import ProfileTag
from .models import Post
from backend.utils import validate_image

class PostListSerializer(serializers.ModelSerializer):
    """Serializer for listing posts."""
    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)

    class Meta:
        model = Post
        fields = ["id", "title", "content", "author", "created_at", "is_owner", "image"]

    def get_is_owner(self, obj):
        """Check if the request user is the owner of the post."""
        request = self.context.get("request")
        return request and request.user.is_authenticated and request.user == obj.author

class PostSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts."""
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
        """Check if the request user is the owner of the post."""
        request = self.context.get("request")
        return request and request.user.is_authenticated and request.user == obj.author

    def get_tagged_users(self, obj):
        """Get the profile names of tagged users."""
        return [tag.tagged_user.profile_name for tag in obj.tags.all()]

    def validate_image(self, value):
        """Validate the image field."""
        return validate_image(value)

    def validate_title(self, value):
        """Ensure the title is unique."""
        if Post.objects.filter(title=value).exists():
            raise ValidationError("A post with this title already exists.")
        return value

    def create(self, validated_data):
        """Create a new post with tags."""
        tags_data = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        self._handle_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        """Update an existing post with tags."""
        tags_data = validated_data.pop("tags", [])
        instance = super().update(instance, validated_data)
        self._handle_tags(instance, tags_data)
        return instance

    def validate_tags(self, value):
        for tag_name in value:
            if not CustomUser.objects.filter(profile_name=tag_name).exists():
                raise serializers.ValidationError(f"User '{tag_name}' does not exist.")
        return value


    def _handle_tags(self, post, tags_data):
        """Handle the creation and assignment of tags."""
        tag_objects = []
        for tag_name in tags_data:
            tagged_user = CustomUser.objects.filter(profile_name=tag_name).first()
            if not tagged_user:
                raise serializers.ValidationError({"tags": f"User '{tag_name}' does not exist."})
            tag, created = ProfileTag.objects.get_or_create(
                tagged_user=tagged_user,
                tagger=post.author,
                content_type=ContentType.objects.get_for_model(Post),
                object_id=post.id,
            )
            tag_objects.append(tag)
        post.tags.set(tag_objects)