from rest_framework import serializers
from django.contrib.auth import get_user_model
from cloudinary.forms import CloudinaryFileField
from .models import Profile
from popularity.models import PopularityMetrics
from backend.utils import validate_image

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    popularity_score = serializers.SerializerMethodField()
    image = CloudinaryFileField(
        options={
            "folder": "profiles",
            "format": "webp",
            "quality": "auto:eco",
            "crop": "limit",
            "width": 1000,
            "height": 1000,
        },
        required=False,
    )

    class Meta:
        model = Profile
        fields = [
            "id",
            "user_id",
            "profile_name",
            "bio",
            "image",
            "popularity_score",
            "follower_count",
            "following_count",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "profile_name",
            "popularity_score",
            "follower_count",
            "following_count",
        ]
        
    def get_popularity_score(self, obj):
        try:
            return obj.user.popularity_metrics.popularity_score
        except PopularityMetrics.DoesNotExist:
            return 0.0

    def validate_image(self, value):
        """Validate the uploaded image."""
        return validate_image(value)

    def update(self, instance, validated_data):
        instance.bio = validated_data.get("bio", instance.bio)
        if "image" in validated_data:
            instance.image = validated_data["image"]
        instance.save()
        return instance
    
    