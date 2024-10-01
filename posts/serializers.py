from rest_framework import serializers
from .models import Post
from tags.serializers import ProfileTagSerializer
from ratings.models import Rating
from ratings.serializers import RatingSerializer
from comments.serializers import CommentSerializer

from django.contrib.contenttypes.models import ContentType
from tags.models import ProfileTag
from accounts.models import CustomUser


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
        Check if the request user is the author.
        """
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer with custom behavior based on user permissions.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            excluded_fields = ['content', 'tags', 'comments']
            for field in excluded_fields:
                self.fields.pop(field, None)
        if not user or not user.is_staff and not user.is_superuser:
            self.fields['is_approved'].read_only = True
        else:
            self.fields['is_approved'].read_only = False

    def perform_update(self, serializer):
        """
        Custom update behavior based on user permissions.
        """
        user = self.context.get('request').user
        if user.is_staff or user.is_superuser:
            serializer.save()
        elif user == serializer.instance.author:
            instance = serializer.save()
            instance.is_approved = False
            instance.save(update_fields=['is_approved'])
        else:
            raise serializers.ValidationError("You don't have permission to edit this post.")

    def to_representation(self, instance):
        """
        Add image URL to representation.
        """
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
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
        Validate image format.
        """
        if not value.name.lower().endswith(('jpg', 'jpeg', 'png', 'gif')):
            raise serializers.ValidationError("Invalid image format")
        return value

    def get_user_rating(self, obj):
        """
        Get the rating given by the request user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = Rating.objects.filter(post=obj, user=request.user).first()
            if rating:
                return RatingSerializer(rating).data
        return None