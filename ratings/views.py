from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from posts.models import Post
from .models import Rating
from .serializers import RatingSerializer
from posts.tasks import update_post_stats
from .messages import STANDARD_MESSAGES


class CreateOrUpdateRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post = serializer.validated_data["post"]
        if not post.is_approved:
            return Response(
                STANDARD_MESSAGES["POST_NOT_APPROVED"],
                status=status.HTTP_400_BAD_REQUEST,
            )

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            post=post,
            defaults={"value": serializer.validated_data["value"]},
        )

        # Call the update_post_stats task
        update_post_stats.delay(post.id)

        message = (
            STANDARD_MESSAGES["RATING_CREATED_SUCCESS"]
            if created
            else STANDARD_MESSAGES["RATING_UPDATED_SUCCESS"]
        )
        return Response(
            {
                "data": self.get_serializer(rating).data,
                "message": message["message"],
                "type": message["type"],
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
