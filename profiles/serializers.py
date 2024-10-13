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

        # Add tags to the representation
        representation['tags'] = self.get_tags(instance)

        return representation

    def get_tags(self, obj):
        """
        Retrieve tags associated with the user.
        """
        return list(ProfileTag.objects.filter(
            tagged_user=obj.user
        ).values_list('tagger__profile_name', flat=True))

    def validate_tags(self, tags):
        """
        Ensure that all tagged users exist.
        """
        for tag in tags:
            if not User.objects.filter(profile_name=tag).exists():
                raise serializers.ValidationError(f"User '{tag}' does not exist.")
        return tags

    def get_posts(self, obj):
        """
        Retrieve a list of the user's posts.
        """
        return Post.objects.filter(author=obj.user).values("id", "title", "content")

    def update(self, instance, validated_data):
        """
        Update the Profile instance and manage the tag updates.
        """
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)

        if tags is not None:
            # Delete existing tags for the user
            ProfileTag.objects.filter(tagged_user=instance.user).delete()

            # Create new tags
            for tag_name in tags:
                tagger = User.objects.filter(profile_name=tag_name).first()
                if tagger:
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

