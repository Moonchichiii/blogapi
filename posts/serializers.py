from rest_framework import serializers
from .models import Post
from tags.serializers import ProfileTagSerializer
from ratings.models import Rating
from ratings.serializers import RatingSerializer
from comments.serializers import CommentSerializer

class LimitedPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.profile_name', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'author_name']

class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.profile_name', read_only=True)
    is_owner = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)
    tags = ProfileTagSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(source='get_average_rating', read_only=True)
    total_ratings = serializers.IntegerField(source='get_total_ratings', read_only=True)
    user_rating = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = '__all__'
        extra_kwargs = {
            'author': {'required': False},
        }

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.author if request and request.user.is_authenticated else False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            excluded_fields = ['content', 'tags', 'comments']
            for field in excluded_fields:
                self.fields.pop(field, None)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)

    def get_user_rating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = Rating.objects.filter(post=obj, user=request.user).first()
            if rating:
                return RatingSerializer(rating).data
        return None