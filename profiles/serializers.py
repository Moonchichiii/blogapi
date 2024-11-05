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
    profile_name = serializers.CharField(read_only=True)
    popularity_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            "profile_name",
            "bio",
            "image",
            "popularity_score",
            "follower_count",
            "following_count",
        ]
        read_only_fields = [
            "popularity_score",
            "follower_count",
            "following_count",
            "profile_name",
        ]

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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Transform image data if it exists
        if data.get('image'):
            data['image'] = {
                'url': instance.image.url,
                'thumbnail': f"{instance.image.url.replace('/upload/', '/upload/c_thumb,h_200,w_200/')}"
            }
        else:
            data['image'] = {
                'url': None,
                'thumbnail': None
            }
        
        return data