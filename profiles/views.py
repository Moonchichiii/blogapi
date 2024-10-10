from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import ProfileSerializer, PopularFollowerSerializer
from .models import Profile
from backend.permissions import IsOwnerOrReadOnly


class ProfileList(generics.ListAPIView):
    """List all profiles with caching."""
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = {
            'message': "Profiles retrieved successfully.",
            'type': "success",
            'data': response.data
        }
        return response

    def get_queryset(self):
        return Profile.objects.all().order_by('-popularity_score', '-follower_count')


class ProfileDetail(generics.RetrieveAPIView):
    """Retrieve a specific profile by user ID."""
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'
    queryset = Profile.objects.all()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'message': "Profile retrieved successfully.",
                'type': "success",
                'data': serializer.data
            })
        except Profile.DoesNotExist:
            return Response({
                'message': "Profile not found.",
                'type': "error"
            }, status=status.HTTP_404_NOT_FOUND)


class CurrentUserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the current user's profile."""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    def perform_update(self, serializer):
        serializer.save()
        return Response({
            'message': "Profile updated successfully.",
            'type': "success",
            'data': serializer.data
        })

class PopularFollowersView(generics.ListAPIView):
    """List popular followers of a user."""
    serializer_class = PopularFollowerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Profile.objects.filter(user__followers__follower_id=user_id).order_by('-popularity_score')[:10]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'message': "Popular followers retrieved successfully.",
            'type': "success",
            'data': serializer.data
        })
