from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from comments.models import Comment
from posts.models import Post
from .models import ProfileTag

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class ProfileTagSerializer(serializers.ModelSerializer):
    """Serializer for ProfileTag model."""
    tagger_name = serializers.CharField(source='tagger.profile_name', read_only=True)
    tagged_user_name = serializers.CharField(source='tagged_user.profile_name', read_only=True)

    class Meta:
        model = ProfileTag
        fields = ['id', 'tagged_user', 'tagged_user_name', 'tagger', 'tagger_name', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'tagger', 'tagger_name', 'created_at']

    def validate(self, attrs):
        """Validate ProfileTag data."""
        request = self.context.get('request')
        tagged_user = attrs.get('tagged_user')
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')

        if tagged_user == request.user:
            raise ValidationError({'message': _("You cannot tag yourself.")})

        valid_models = [Post, Comment]
        model_class = content_type.model_class()
        if model_class not in valid_models:
            raise ValidationError({'message': _("Invalid content type for tagging.")})

        try:
            model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            raise ValidationError({'message': _("Invalid object.")})

        if ProfileTag.objects.filter(tagged_user=tagged_user, content_type=content_type, object_id=object_id).exists():
            raise ValidationError({'message': _("Duplicate tag: You have already tagged this user on this object.")})

        return attrs

    def create(self, validated_data):
        """Assign request user as tagger and create ProfileTag instance."""
        validated_data['tagger'] = self.context['request'].user
        return super().create(validated_data)

