"""
Serializers for the Post model.
"""

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from accounts.models import CustomUser
from tags.models import ProfileTag
from .models import Post


class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing posts with author and ownership details.
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
        return request.user == obj.author if request and request.user.is_authenticated else False


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed post data including tagged users and image.
    """

    author = serializers.CharField(source="author.profile_name", read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tagged_users = serializers.SerializerMethodField(read_only=True)
    tags = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Post
        fields = [
            "id", "title", "content", "image", "author", "created_at",
            "average_rating", "is_owner", "tagged_users", "tags"
        ]
        read_only_fields = ["id", "author", "created_at", "average_rating"]

    def get_tagged_users(self, obj):
        """
        Return a list of profile names of the users tagged in the post.
        """
        return [tag.tagged_user.profile_name for tag in obj.tags.all()]

    def create(self, validated_data):
        """
        Create a new post and handle tag creation.
        """
        tags_data = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        self._handle_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        """
        Update an existing post and handle tag updates.
        """
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        self._handle_tags(instance, tags_data)
        return instance

    def validate(self, attrs):
        """
        Validate the title and image fields.
        """
        if "title" in attrs:
            existing_posts = Post.objects.filter(title=attrs["title"])
            if self.instance:
                existing_posts = existing_posts.exclude(pk=self.instance.pk)
            if existing_posts.exists():
                raise serializers.ValidationError({"title": "A post with this title already exists."})
        return attrs

    def validate_image(self, value):
        """
        Ensure the image file is of valid format and size.
        """
        if value and not value.name.lower().endswith(("jpg", "jpeg", "png", "gif", "webp")):
            raise serializers.ValidationError("Invalid image format.")
        if value and value.size > 2 * 1024 * 1024:  # 2 MB limit
            raise serializers.ValidationError("Image must be less than 2MB.")
        return value

    def _handle_tags(self, post, tags_data):
        """
        Process the tag data for the post.
        """
        content_type = ContentType.objects.get_for_model(Post)
        # Remove old tags not in the new tags_data
        ProfileTag.objects.filter(content_type=content_type, object_id=post.id).exclude(
            tagged_user__profile_name__in=tags_data
        ).delete()

        existing_tags = set(
            ProfileTag.objects.filter(content_type=content_type, object_id=post.id).values_list(
                "tagged_user__profile_name", flat=True
            )
        )

        # Add new tags
        new_tags = []
        for tag_name in tags_data:
            if tag_name not in existing_tags:
                tagged_user = CustomUser.objects.filter(profile_name=tag_name).first()
                if tagged_user:
                    new_tag = ProfileTag(
                        tagged_user=tagged_user,
                        tagger=post.author,
                        content_type=content_type,
                        object_id=post.id
                    )
                    new_tags.append(new_tag)
                else:
                    raise serializers.ValidationError({"tags": f"User '{tag_name}' does not exist."})
        if new_tags:
            ProfileTag.objects.bulk_create(new_tags, ignore_conflicts=True)


class LimitedPostSerializer(serializers.ModelSerializer):
    """
    Serializer for listing limited post info including author and image.
    """

    author = serializers.CharField(source="author.profile_name", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "title", "author", "image_url"]

    def get_image_url(self, obj):
        """
        Get the URL of the post's image if available.
        """
        return obj.image.url if obj.image and hasattr(obj.image, "url") else None
