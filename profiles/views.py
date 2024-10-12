from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Profile
from .serializers import ProfileSerializer, PopularFollowerSerializer
from .messages import profile_success_response
from backend.permissions import IsOwnerOrReadOnly

CACHE_TIMEOUT = 60 * 15

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProfileList(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Profile.objects.prefetch_related('user__followers').order_by('-popularity_score', '-follower_count')

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ProfileDetail(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly] 
    lookup_field = 'user_id'
    queryset = Profile.objects.select_related('user').prefetch_related('user__posts')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'data': serializer.data,
            'message': 'Profile retrieved successfully.',
            'type': 'success'
        }, status=status.HTTP_200_OK)

class CurrentUserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return self.request.user.profile

    def perform_update(self, serializer):
        image_changed = 'image' in serializer.validated_data
        old_image = None
        if image_changed:
            old_image = self.get_object().image
        
        serializer.save()

        if old_image:
            old_image.delete()

        return profile_success_response("Your profile has been updated.", serializer.data)

class PopularFollowersView(generics.ListAPIView):
    """List popular followers of a user."""
    serializer_class = PopularFollowerSerializer
    permission_classes = [AllowAny]

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Profile.objects.filter(user__followers__follower_id=user_id).select_related('user').order_by('-popularity_score')[:10]
