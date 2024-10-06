from typing import Optional
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from posts.models import Post
from posts.tasks import update_post_stats
from .models import Rating
from .serializers import RatingSerializer
from .messages import STANDARD_MESSAGES

class CreateOrUpdateRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs) -> Response:
        user = request.user
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            if 'post' in serializer.errors and any('does not exist' in error for error in serializer.errors['post']):
                return self.error_response('POST_NOT_FOUND', status.HTTP_404_NOT_FOUND)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        post = serializer.validated_data.get('post')
        rating_value = serializer.validated_data.get('value')

        if not post.is_approved:
            return self.error_response('POST_NOT_APPROVED', status.HTTP_400_BAD_REQUEST)

        rating, created = Rating.objects.update_or_create(
            user=user, post=post,
            defaults={'value': rating_value}
        )

        update_post_stats.delay(post.id)

        serializer = self.get_serializer(rating)
        message_key = 'RATING_CREATED_SUCCESS' if created else 'RATING_UPDATED_SUCCESS'
        print(f"Message Key: {message_key}")
        return self.success_response(serializer, message_key, created)

    def error_response(self, message_key: str, status_code: int) -> Response:
        return Response({
            "error": STANDARD_MESSAGES[message_key]['message'],
            "type": STANDARD_MESSAGES[message_key]['type']
        }, status=status_code)

    def success_response(self, serializer, message_key: str, created: bool) -> Response:
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({
            "data": serializer.data,
            "message": STANDARD_MESSAGES[message_key]['message'],
            "type": STANDARD_MESSAGES[message_key]['type']
        }, status=status_code)
