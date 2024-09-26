from rest_framework import serializers
from .models import ProfileTag
from django.contrib.contenttypes.models import ContentType
from posts.models import Post
from comments.models import Comment

class ProfileTagSerializer(serializers.ModelSerializer):
    tagger_name = serializers.CharField(source='tagger.profile_name', read_only=True)
    tagged_user_name = serializers.CharField(source='tagged_user.profile_name', read_only=True)

    class Meta:
        model = ProfileTag
        fields = ['id', 'tagged_user', 'tagged_user_name', 'tagger', 'tagger_name', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['id', 'tagger', 'tagger_name', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        tagged_user = attrs.get('tagged_user')
        content_type = attrs.get('content_type')
        object_id = attrs.get('object_id')

        if tagged_user == request.user:
            raise serializers.ValidationError("You cannot tag yourself.")

        valid_models = [Post, Comment]
        try:
            model_class = content_type.model_class()
            if model_class not in valid_models:
                raise serializers.ValidationError("Invalid content type for tagging.")
        except AttributeError:
            raise serializers.ValidationError("Invalid content type for tagging.")

        try:
            obj = model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            raise serializers.ValidationError("Invalid object.")

        if ProfileTag.objects.filter(
            tagged_user=tagged_user,
            content_type=content_type,
            object_id=object_id
        ).exists():
            raise serializers.ValidationError("Duplicate tag: You have already tagged this user on this object.")

        return attrs

    def create(self, validated_data):
        validated_data['tagger'] = self.context['request'].user
        return super().create(validated_data)