from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from rest_framework import serializers

from tags.models import ProfileTag
from posts.models import Post
from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    bio = serializers.CharField(required=False, max_length=500)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    posts = serializers.SerializerMethodField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Profile
        fields = [
            'id', 'user_id', 'profile_name', 'bio', 'image', 'popularity_score', 'posts', 'tags'
        ]
        read_only_fields = [
            'id', 'user_id', 'profile_name', 'popularity_score'
        ]


    def to_representation(self, instance):
        """
        Customize the representation of the Profile instance.
        """
        representation = super().to_representation(instance)
        
        # Handle F() expressions
        for field in ['follower_count', 'following_count']:
            if isinstance(representation[field], F):
                representation[field] = getattr(instance, field)
        
        # Add tags
        representation['tags'] = self.get_tags(instance)
        
        return representation

    def get_tags(self, obj):
        """
        Get tags of user's posts.
        """
        return list(ProfileTag.objects.filter(
            tagged_user=obj.user
        ).values_list('tagger__profile_name', flat=True))

    def get_is_following(self, obj):
        """
        Check if the current user is following the profile.
        """
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.user.followers.filter(follower=user).exists()
        return False

    def validate_tags(self, tags):
        """
        Ensure that all tagged users exist.
        """
        for tag in tags:
            if not User.objects.filter(profile_name=tag).exists():
                raise serializers.ValidationError(
                    f"User '{tag}' does not exist."
                )
        return tags

    def get_posts(self, obj):
        """
        Return a list of user's posts.
        """
        return Post.objects.filter(
            author=obj.user
        ).values("id", "title", "content")

    def update(self, instance, validated_data):
        """
        Update the Profile instance and manage tag updates.
        """
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)

        if tags is not None:
            # Delete existing tags for this user
            ProfileTag.objects.filter(tagged_user=instance.user).delete()

            # Create new tags, ensuring no duplicates
            for tag_name in tags:
                tagger = User.objects.filter(profile_name=tag_name).first()
                if tagger:
                    # Ensure we don't create duplicate entries
                    if not ProfileTag.objects.filter(
                        tagger=tagger,
                        tagged_user=instance.user,
                        content_type=ContentType.objects.get_for_model(Profile),
                        object_id=instance.id
                    ).exists():
                        ProfileTag.objects.create(
                            tagger=tagger,
                            tagged_user=instance.user,
                            content_type=ContentType.objects.get_for_model(Profile),
                            object_id=instance.id
                        )
        return instance


class PopularFollowerSerializer(serializers.ModelSerializer):
    """
    Serializer for popular followers.
    """
    profile_name = serializers.CharField(source='user.profile_name')
    average_rating = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'profile_name', 'image', 'average_rating', 'comment_count',
            'post_count', 'popularity_score', 'tags'
        ]

    def get_average_rating(self, obj):
        """
        Get average rating of user's posts.
        """
        return obj.user.posts.aggregate(
            Avg('average_rating')
        )['average_rating__avg'] or 0

    def get_post_count(self, obj):
        """
        Get count of user's posts.
        """
        return obj.user.posts.count()

    def get_tags(self, obj):
        """
        Get tags of user's posts.
        """
        return obj.user.tags.values_list('tagged_user__profile_name', flat=True)
