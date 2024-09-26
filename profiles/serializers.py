from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    follower_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()
    popularity_score = serializers.FloatField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    tag_count = serializers.IntegerField(read_only=True)

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
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        user = getattr(request, 'user', None)

        # Hide email if the current user is not the owner of the profile
        if self.instance and user and user.is_authenticated and self.instance.user != user:
            self.fields.pop('email', None)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add image URL if it exists
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def get_is_following(self, obj):
        request = self.context.get('request', None)
        user = getattr(request, 'user', None)
        return user.is_authenticated and obj.user.followers.filter(follower=user).exists() if user else False

    def update(self, instance, validated_data):
        # Update fields if they exist in validated data
        instance.bio = validated_data.get('bio', instance.bio)
        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()
        return instance
