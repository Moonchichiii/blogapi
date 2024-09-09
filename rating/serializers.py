from rest_framework import serializers
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.profile_name', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'user_name', 'post', 'value', 'created_at', 'updated_at']
        read_only_fields = ['user']