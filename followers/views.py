from django.db import transaction
from django.contrib.auth import get_user_model
from django.http import Http404  # Add this import
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Follow
from .serializers import FollowSerializer
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from .signals import invalidate_follower_cache
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class PopularFollowersView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Assuming we retrieve popular profiles based on a follower count threshold
        return Profile.objects.order_by('-follower_count')[:10] 

class FollowerDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Follow.objects.all()  # Define the queryset here for general follow instances

    def get_queryset(self):
        # Optionally, override get_queryset if further filtering is needed
        # Only retrieves follows associated with the provided `user_id`
        return Follow.objects.filter(followed_id=self.kwargs['user_id'])

    def get_object(self):
        # Retrieves a specific follow instance where the user is following another user
        try:
            return Follow.objects.get(
                follower=self.request.user,
                followed_id=self.kwargs['user_id']
            )
        except Follow.DoesNotExist:
            raise Http404("Follow relationship does not exist.")

    def delete(self, request, *args, **kwargs):
        followed_id = request.data.get("followed")
        if not followed_id:
            return Response({"error": "Invalid unfollow request."}, status=status.HTTP_400_BAD_REQUEST)

        follow = Follow.objects.filter(follower=request.user, followed_id=followed_id).first()
        if follow:
            with transaction.atomic():
                follow.delete()
                invalidate_follower_cache(followed_id)  # Invalidate cache on unfollow
                return Response({"message": "Unfollowed successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Not following user."}, status=status.HTTP_400_BAD_REQUEST)
