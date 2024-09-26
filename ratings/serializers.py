from rest_framework import serializers
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'profile_name', 'post', 'post_title', 'value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'profile_name', 'created_at', 'updated_at']

    def validate(self, data):
        if self.instance is None:  # Only check for existing rating on creation
            user = self.context['request'].user
            post = data['post']
            if Rating.objects.filter(user=user, post=post).exists():
                raise serializers.ValidationError("You have already rated this post.")
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)