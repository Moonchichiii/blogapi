from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from accounts.models import CustomUser
from .models import Post
from tags.models import ProfileTag

class PostListSerializer(serializers.ModelSerializer):
    """Serializer for listing posts."""
    author = serializers.CharField(source='author.profile_name', read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'is_owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False

class PostSerializer(serializers.ModelSerializer):
    """Serializer for post details."""
    author = serializers.CharField(source='author.profile_name', read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tagged_users = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'image', 'author', 'created_at',
            'average_rating', 'is_owner', 'tagged_users'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'average_rating']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False

    def get_tagged_users(self, obj):
        """Get users tagged in the post."""
        return [tag.tagged_user.profile_name for tag in obj.tags.all()]

    def validate(self, attrs):
        """Validate the title and image of the post."""
        if 'title' in attrs:
            existing_posts = Post.objects.filter(title=attrs['title'])
            if self.instance:
                existing_posts = existing_posts.exclude(pk=self.instance.pk)
            if existing_posts.exists():
                raise serializers.ValidationError({'title': "A post with this title already exists."})
        return attrs

    def validate_image(self, value):
        """Ensure the image is valid."""
        if value:
            if not value.name.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'webp')):
                raise serializers.ValidationError("Invalid image format.")
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Image must be less than 2MB.")
        return value

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        self._process_tags(post, tags_data)
        return post

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        self._process_tags(instance, tags_data)
        return instance

    def _process_tags(self, post, tags_data):
        content_type = ContentType.objects.get_for_model(Post)
        ProfileTag.objects.filter(content_type=content_type, object_id=post.id).exclude(tagged_user__profile_name__in=tags_data).delete()

        existing_tags = set(ProfileTag.objects.filter(content_type=content_type, object_id=post.id).values_list('tagged_user__profile_name', flat=True))

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
    """Serializer for limited post info."""
    author = serializers.CharField(source='author.profile_name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'author', 'image_url']

    def get_image_url(self, obj):
        return obj.image.url if obj.image and hasattr(obj.image, 'url') else None