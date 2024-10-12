from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from posts.models import Post
from .models import Rating
from .serializers import RatingSerializer
from celery import shared_task

class CreateOrUpdateRatingView(generics.CreateAPIView):
    """
    View to create or update a rating for a post.
    """
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        post = serializer.validated_data.get('post')
        rating_value = serializer.validated_data.get('value')

        # Ensure only approved posts can be rated
        if not post.is_approved:
            return Response({
                'message': 'You cannot rate an unapproved post.',
                'type': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has already rated the post
        rating, created = Rating.objects.update_or_create(
            user=self.request.user,
            post=post,
            defaults={'value': rating_value}
        )

        # Asynchronous task to update post stats
        update_post_stats.delay(post.id)

        # Return appropriate response
        message = 'Rating created successfully.' if created else 'Rating updated successfully.'
        return Response({
            'data': self.get_serializer(rating).data,
            'message': message,
            'type': 'success'
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
