from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from rest_framework import serializers
from comments.models import Comment
from posts.models import Post
from .models import ProfileTag
from .messages import STANDARD_MESSAGES

class ProfileTagSerializer(serializers.ModelSerializer):
    """
    Serializer for ProfileTag model.
    """
    tagger_name = serializers.CharField(source='tagger.profile_name', read_only=True)
    tagged_user_name = serializers.CharField(source='tagged_user.profile_name', read_only=True)

    class Meta:
        model = ProfileTag
        fields = ['id', 'tagged_user', 'tagged_user_name', 'tagger', 'tagger_name', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'tagger', 'tagger_name', 'created_at']

    def validate(self, attrs):
        """
        Validate the ProfileTag data.
        """
        request = self.context.get('request')
        tagged_user = attrs.get('tagged_user')
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')

        if tagged_user == request.user:
            raise serializers.ValidationError({'message': STANDARD_MESSAGES['CANNOT_TAG_SELF']['message']})

        valid_models = [Post, Comment]
        model_class = content_type.model_class()
        if model_class not in valid_models:
            raise serializers.ValidationError({'message': STANDARD_MESSAGES['INVALID_CONTENT_TYPE']['message']})

        try:
            model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            raise serializers.ValidationError({'message': "Invalid object."})

        if ProfileTag.objects.filter(tagged_user=tagged_user, content_type=content_type, object_id=object_id).exists():
            raise serializers.ValidationError({'message': STANDARD_MESSAGES['DUPLICATE_TAG']['message']})

        return attrs

    def create(self, validated_data):
        """
        Assign the request user as the tagger and create the ProfileTag instance.
        """
        validated_data['tagger'] = self.context['request'].user
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'message': STANDARD_MESSAGES['DUPLICATE_TAG']['message']})
