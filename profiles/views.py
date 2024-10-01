from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import ProfileSerializer
from .models import Profile
from backend.permissions import IsOwnerOrReadOnly


class ProfileList(generics.ListAPIView):
    """
    API view to retrieve list of profiles.
    """
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        """
        Retrieve a cached list of profiles.
        """
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return profiles ordered by popularity score and follower count.
        """
        return Profile.objects.all().order_by('-popularity_score', '-follower_count')


class ProfileDetail(generics.RetrieveAPIView):
    """
    API view to retrieve a profile by user ID.
    """
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'
    queryset = Profile.objects.all()


class CurrentUserProfile(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve and update the current user's profile.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        """
        Retrieve the profile of the current user.
        """
        return Profile.objects.get(user=self.request.user)

    def perform_update(self, serializer):
        """
        Save the updated profile.
        """
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve the current user's profile.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)