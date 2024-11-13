import logging
from django.db.models import OuterRef, Subquery, Exists, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Profile
from .serializers import ProfileSerializer
from followers.models import Follow
from popularity.models import PopularityMetrics
from backend.permissions import IsProfileOwnerOrAdmin, BasePermission

CACHE_TIMEOUT = 60 * 30
logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    """Custom pagination settings."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class ProfileListView(generics.ListAPIView):
    """List and filter profiles with enhanced permission handling."""
    serializer_class = ProfileSerializer
    permission_classes = [BasePermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        """Return filtered and annotated queryset."""
        user = self.request.user
        filter_type = self.request.query_params.get('filter', 'popular')
        popularity_subquery = PopularityMetrics.objects.filter(
            user=OuterRef('user')
        ).values('popularity_score')[:1]
        queryset = Profile.objects.annotate(
            popularity_score=Subquery(popularity_subquery)
        )
        if not user.is_authenticated:
            queryset = queryset.filter(user__is_active=True)
        elif filter_type == 'followed' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(Follow.objects.filter(follower=user, followed=OuterRef('user')))
            )
        elif user.has_permission_to(self.request, 'manage_users'):
            pass
        else:
            queryset = queryset.filter(
                Q(user__is_active=True) | Q(user=user)
            )
        return queryset.order_by('-popularity_score', 'user__profile_name')

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        """Cache and paginate profile listings."""
        response = super().list(request, *args, **kwargs)
        response.data.update({
            "message": "Profiles retrieved successfully",
            "type": "success"
        })
        return response

class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a profile with enhanced permissions."""
    queryset = Profile.objects.select_related('user')
    serializer_class = ProfileSerializer
    permission_classes = [IsProfileOwnerOrAdmin]
    lookup_field = "user__id"
    lookup_url_kwarg = "user_id"

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a profile with enhanced response."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Profile retrieved successfully",
            "type": "success"
        })

    def update(self, request, *args, **kwargs):
        """Update a profile with enhanced validation."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if 'profile_name' in request.data:
            if Profile.objects.filter(
                profile_name=request.data['profile_name']
            ).exclude(user=instance.user).exists():
                return Response({
                    "message": "This profile name is already taken.",
                    "type": "error"
                }, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return Response({
            "data": serializer.data,
            "message": "Profile updated successfully",
            "type": "success"
        })

    def perform_update(self, serializer):
        """Save the updated profile."""
        serializer.save()
