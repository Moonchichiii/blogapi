from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.profile_name", read_only=True)
    author_image = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "author_image", "content", "created_at", "updated_at", "is_approved"]
        read_only_fields = ["id", "author", "created_at", "updated_at", "is_approved", "post"]

    def get_author_image(self, obj):
        return obj.author.profile.image.url if obj.author.profile.image else None

    def validate_post(self, value):
        if not value.is_approved:
            raise serializers.ValidationError("Cannot comment on an unapproved post.")
        return value