from django.db import transaction
from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Follow
from .serializers import FollowSerializer
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from .signals import invalidate_follower_cache
from backend.permissions import IsOwnerOrAdmin

User = get_user_model()

class PopularFollowersView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Retrieve popular profiles based on follower count
        return Profile.objects.order_by('-follower_count')[:10]

class FollowerDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Follow.objects.all()

    def get_queryset(self):
        return Follow.objects.filter(followed_id=self.kwargs['user_id'])

    def get_object(self):
        try:
            return Follow.objects.get(
                follower=self.request.user,
                followed_id=self.kwargs['user_id']
            )
        except Follow.DoesNotExist:
            raise Http404("Follow relationship does not exist.")

    def delete(self, request, *args, **kwargs):
        follow = self.get_object()
        with transaction.atomic():
            follow.delete()
            invalidate_follower_cache(follow.followed.id)
            invalidate_follower_cache(follow.follower.id)
            return Response({"message": "Unfollowed successfully."}, status=status.HTTP_200_OK)
