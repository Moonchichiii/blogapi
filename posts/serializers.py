from rest_framework import serializers
from .models import Post
from tags.serializers import ProfileTagSerializer
from ratings.models import Rating

class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.profile_name', read_only=True)
    image = serializers.ImageField(required=False)
    tags = ProfileTagSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_ratings = serializers.IntegerField(read_only=True)
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'author_name', 'title', 'content', 'image', 'created_at', 'updated_at', 'is_approved', 'tags', 'average_rating', 'total_ratings', 'user_rating']
        read_only_fields = ['id', 'author', 'author_name', 'created_at', 'updated_at', 'is_approved', 'tags', 'average_rating', 'total_ratings', 'user_rating']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
    
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = obj.ratings.get(user=request.user)
                return RatingSerializer(rating).data
            except Rating.DoesNotExist:
                return None
        return None