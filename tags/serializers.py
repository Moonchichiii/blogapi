from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from comments.models import Comment
from posts.models import Post
from .models import ProfileTag

class ProfileTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileTag
        fields = ["id", "tagged_user", "content_type", "object_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        tagged_user = attrs.get("tagged_user")
        content_type = attrs.get("content_type")
        object_id = attrs.get("object_id")

        if tagged_user == request.user:
            raise serializers.ValidationError(
                {"non_field_errors": ["You cannot tag yourself."]}
            )

        model_class = content_type.model_class()
        valid_models = [Post, Comment]

        if model_class not in valid_models:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid content type."]}
            )

        try:
            model_class.objects.get(id=object_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid object ID."]}
            )

        if ProfileTag.objects.filter(
            tagged_user=tagged_user, content_type=content_type, object_id=object_id
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["Duplicate tag detected."]}
            )

        return attrs