from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import ProfileSerializer
from .models import Profile
from backend.permissions import IsOwnerOrReadOnly
from .messages import STANDARD_MESSAGES


class ProfileList(generics.ListAPIView):
    """
    API view to retrieve a list of profiles.
    """
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        """
        Retrieve a cached list of profiles.
        """
        response = super().list(request, *args, **kwargs)
        response.data.update({
            'message': STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['type']
        })
        return response

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

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a profile by user ID.
        """
        try:
            response = super().retrieve(request, *args, **kwargs)
            response.data.update({
                'message': STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['type']
            })
            return response
        except Profile.DoesNotExist:
            return Response({
                'message': STANDARD_MESSAGES['PROFILE_NOT_FOUND']['message'],
                'type': STANDARD_MESSAGES['PROFILE_NOT_FOUND']['type']
            }, status=status.HTTP_404_NOT_FOUND)


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
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve the current user's profile.
        """
        profile = self.get_object()
        if profile:
            serializer = self.get_serializer(profile)
            return Response({
                'data': serializer.data,
                'message': STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['PROFILE_RETRIEVED_SUCCESS']['type']
            }, status=status.HTTP_200_OK)
        return Response({
            'message': STANDARD_MESSAGES['PROFILE_NOT_FOUND']['message'],
            'type': STANDARD_MESSAGES['PROFILE_NOT_FOUND']['type']
        }, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        """
        Update the current user's profile.
        """
        profile = self.get_object()
        if profile:
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response({
                    'data': serializer.data,
                    'message': STANDARD_MESSAGES['PROFILE_UPDATED_SUCCESS']['message'],
                    'type': STANDARD_MESSAGES['PROFILE_UPDATED_SUCCESS']['type']
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': STANDARD_MESSAGES['PROFILE_NOT_FOUND']['message'],
            'type': STANDARD_MESSAGES['PROFILE_NOT_FOUND']['type']
        }, status=status.HTTP_404_NOT_FOUND)
