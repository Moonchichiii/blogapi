from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model.
    """
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    is_following = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user_id', 'bio', 'image', 'follower_count', 'following_count',
            'popularity_score', 'is_following', 'profile_name', 'email', 'comment_count', 'tag_count'
        ]
        read_only_fields = [
            'id', 'follower_count', 'following_count', 'popularity_score',
            'profile_name', 'email', 'comment_count', 'tag_count'
        ]

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer and conditionally remove the email field.
        """
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        user = getattr(request, 'user', None)
        if self.instance and user and (not user.is_authenticated or self.instance.user != user):
            self.fields.pop('email', None)

    def to_representation(self, instance):
        """
        Customize the representation of the instance.
        """
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def get_is_following(self, obj):
        """
        Determine if the current user is following the profile user.
        """
        request = self.context.get('request', None)
        user = getattr(request, 'user', None)
        if user:
            return user.is_authenticated and obj.user.followers.filter(follower=user).exists()
        return False

    def update(self, instance, validated_data):
        """
        Update the profile instance with validated data.
        """
        instance.bio = validated_data.get('bio', instance.bio)
        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()
        return instance