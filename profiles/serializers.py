from rest_framework import serializers
from cloudinary.forms import CloudinaryFileField
from .models import Profile
from popularity.models import PopularityMetrics
from backend.utils import validate_image

class ProfileSerializer(serializers.ModelSerializer):
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
    image_url = serializers.SerializerMethodField()
    popularity_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            "bio",
            "image",
            "image_url",
            "popularity_score",
            "follower_count",
            "following_count",
        ]
        read_only_fields = [
            "popularity_score",
            "follower_count",
            "following_count",
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_popularity_score(self, obj):
        try:
            return obj.user.popularity_metrics.popularity_score
        except (AttributeError, PopularityMetrics.DoesNotExist):
            return 0.0

    def validate_image(self, value):
        return validate_image(value)

    def update(self, instance, validated_data):
        instance.bio = validated_data.get("bio", instance.bio)
        if "image" in validated_data:
            instance.image = validated_data["image"]
        instance.save()
        return instance
