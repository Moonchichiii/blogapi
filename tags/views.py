from rest_framework import generics, permissions
from .models import ProfileTag
from .serializers import ProfileTagSerializer
from django.contrib.contenttypes.models import ContentType
from posts.models import Post
from comments.models import Comment

class CreateProfileTag(generics.CreateAPIView):
    serializer_class = ProfileTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        content_type_id = self.request.data.get('content_type')
        object_id = self.request.data.get('object_id')

        content_type = ContentType.objects.get_for_id(content_type_id)
        if content_type.model_class() not in [Post, Comment]:
            raise serializers.ValidationError("Invalid content type for tagging")

        serializer.save(
            tagger=self.request.user,
            content_type=content_type,
            object_id=object_id
        )
