from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    follower_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    popularity_score = serializers.FloatField(read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'bio', 'image', 'follower_count', 'following_count', 'popularity_score', 'is_following', 'profile_name', 'email']
        read_only_fields = ['id', 'follower_count', 'following_count', 'popularity_score', 'profile_name', 'email']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user.followers.filter(follower=request.user).exists()
        return False


    def update(self, instance, validated_data):
        instance.bio = validated_data.get('bio', instance.bio)
        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()
        return instance