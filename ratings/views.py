from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Rating
from .serializers import RatingSerializer
from .tasks import update_post_stats


class CreateOrUpdateRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        post = serializer.validated_data["post"]
        rating, created = Rating.objects.update_or_create(
            user=request.user,
            post=post,
            defaults={"value": serializer.validated_data["value"]},
        )        
        
        update_post_stats.delay(post.id)
        
        message = "Rating created successfully." if created else "Rating updated successfully."
        return Response(
            {
                "data": self.get_serializer(rating).data,
                "message": message,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class GetUserRatingView(generics.RetrieveAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        post_id = self.kwargs['post_id']
        user = self.request.user
        try:
            return Rating.objects.get(post_id=post_id, user=user)
        except Rating.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        rating = self.get_object()
        if rating:
            serializer = self.get_serializer(rating)
            return Response(
                {
                    "data": serializer.data,
                    "message": "Rating retrieved successfully."
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "data": {"value": None},
                    "message": "Rating not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )