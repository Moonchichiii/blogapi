from rest_framework import serializers
from .models import Follow

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']

    def create(self, validated_data):
        return super().create(validated_data)


    def update(self, instance, validated_data):        
        return super().update(instance, validated_data)
