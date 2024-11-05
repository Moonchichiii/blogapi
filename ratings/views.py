# views.py
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
        
        return Response(
            {
                "data": self.get_serializer(rating).data,
                "message": "Rating created successfully." if created else "Rating updated successfully.",
                "type": "success"
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

class GetPostRatingView(generics.RetrieveAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        try:
            return Rating.objects.get(
                post_id=self.kwargs['post_id'],
                user=self.request.user
            )
        except Rating.DoesNotExist:
            return None
    
    def get(self, request, *args, **kwargs):
        rating = self.get_object()
        if not rating:
            return Response(
                {
                    "data": None,
                    "message": "No rating found",
                    "type": "info"
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(rating)
        return Response(
            {
                "data": serializer.data,
                "message": "Rating retrieved successfully",
                "type": "success"
            },
            status=status.HTTP_200_OK
        )

