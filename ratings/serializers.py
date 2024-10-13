from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from posts.models import Post
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='user.profile_name', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.filter(is_approved=True))

    class Meta:
        model = Rating
        fields = ['post', 'value']

    def validate_value(self, value):
        """Ensure rating value is between 1 and 5."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError(_("Rating value must be between 1 and 5."))
        return value
