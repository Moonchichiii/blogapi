"""
Serializers for the blog API.
"""

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from accounts.models import CustomUser
from comments.serializers import CommentSerializer
from ratings.models import Rating
from ratings.serializers import RatingSerializer
from tags.models import ProfileTag
from .models import Post
from .messages import STANDARD_MESSAGES

class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing posts.
    """
    author_name = serializers.CharField(source='author.profile_name', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'author_name', 'created_at', 'average_rating', 'slug']

class LimitedPostSerializer(serializers.ModelSerializer):
    """
    Serializer for limited post details.
    """
    author_name = serializers.CharField(source='author.profile_name', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'author_name']

class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed post information.
    """
    author_name = serializers.CharField(source='author.profile_name', read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    average_rating = serializers.FloatField(source='get_average_rating', read_only=True)
    total_ratings = serializers.IntegerField(source='get_total_ratings', read_only=True)
    user_rating = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = '__all__'
        extra_kwargs = {
            'author': {'required': False},
        }

    def get_is_owner(self, obj):
        """
        Check if the request user is the owner of the post.
        """
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError({
                'message': STANDARD_MESSAGES['DUPLICATE_TAG_ERROR']['message'],
                'type': STANDARD_MESSAGES['DUPLICATE_TAG_ERROR']['type']
            })

        # Create the post
        post = Post.objects.create(**validated_data)
        content_type = ContentType.objects.get_for_model(Post)
        for tag_name in tags_data:
            tagged_user = CustomUser.objects.filter(profile_name=tag_name).first()
            if tagged_user:
                ProfileTag.objects.create(
                    tagged_user=tagged_user,
                    tagger=post.author,
                    content_type=content_type,
                    object_id=post.id
                )
        return post

    def validate_image(self, value):
        """
        Validate the image format.
        """
        if value and not value.name.lower().endswith(('jpg', 'jpeg', 'png', 'gif')):
            raise serializers.ValidationError(
                STANDARD_MESSAGES['IMAGE_FORMAT_INVALID']['message']
            )
        return value

    def get_user_rating(self, obj):
        """
        Get the rating given by the request user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = Rating.objects.filter(post=obj, user=request.user).first()
            return RatingSerializer(rating).data if rating else None
        return None

    def perform_update(self, instance, validated_data):
        user = self.context['request'].user
        if not (user.is_staff or user.is_superuser):
            validated_data['is_approved'] = False
        return super().perform_update(instance, validated_data)
