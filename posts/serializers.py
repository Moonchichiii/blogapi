from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from accounts.models import CustomUser
from comments.serializers import CommentSerializer
from ratings.serializers import RatingSerializer
from tags.models import ProfileTag
from .models import Post


class PostListSerializer(serializers.ModelSerializer):
    """Serializer for listing posts with basic details."""
    author = serializers.CharField(source='author.profile_name', read_only=True)
    is_owner = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(read_only=True)
    tag_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'author', 'created_at', 'average_rating', 'is_owner', 'comment_count', 'tag_count']

    def get_is_owner(self, obj):
        """Check if the current user is the owner of the post."""
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False


class PostSerializer(serializers.ModelSerializer):
    """Serializer for detailed post information."""
    author = serializers.CharField(source='author.profile_name', read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    tagged_users = serializers.SerializerMethodField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    tags_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(source='average_rating', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'image', 'author', 'created_at', 'comments',
            'comments_count', 'tags_count', 'average_rating', 'is_owner', 'tagged_users'
        ]

    def get_is_owner(self, obj):
        """Check if the current user is the owner of the post."""
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False

    def get_tagged_users(self, obj):
        """Get the profile names of tagged users."""
        return [tag.tagged_user.profile_name for tag in obj.tags.all()]

    def validate_tags(self, value):
        """Validate that there are no duplicate tags."""
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate tags are not allowed.")
        return value

    def validate(self, attrs):
        """Validate the post data."""
        if 'title' in attrs:
            existing_posts = Post.objects.filter(title=attrs['title'])
            if self.instance:
                existing_posts = existing_posts.exclude(pk=self.instance.pk)
            if existing_posts.exists():
                raise serializers.ValidationError({'title': "A post with this title already exists."})
        return attrs

    def validate_image(self, value):
        """Validate the image format and size."""
        if value:
            if not value.name.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'webp')):
                raise serializers.ValidationError("Invalid image format.")
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Image must be less than 2MB.")
        return value

    def create(self, validated_data):
        """Create a new post."""
        tags_data = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        self._process_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        """Update an existing post."""
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        self._process_tags(instance, tags_data)
        return instance

    def _process_tags(self, post, tags_data):
        """Process the tags for a post."""
        content_type = ContentType.objects.get_for_model(Post)

        # Remove tags not in the new list
        ProfileTag.objects.filter(
            content_type=content_type, object_id=post.id
        ).exclude(tagged_user__profile_name__in=tags_data).delete()

        existing_tags = set(ProfileTag.objects.filter(
            content_type=content_type, object_id=post.id
        ).values_list('tagged_user__profile_name', flat=True))

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
                    raise serializers.ValidationError({
                        'tags': [f"User with profile name '{tag_name}' does not exist."]
                    })
        if new_tags:
            ProfileTag.objects.bulk_create(new_tags, ignore_conflicts=True)


class LimitedPostSerializer(serializers.ModelSerializer):
    """Serializer for limited post information."""
    author = serializers.CharField(source='author.profile_name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'author', 'image_url']

    def get_image_url(self, obj):
        """Get the URL of the post's image."""
        return obj.image.url if obj.image and hasattr(obj.image, 'url') else None
