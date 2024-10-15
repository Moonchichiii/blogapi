import logging
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Profile
from .serializers import ProfileSerializer
from popularity.models import PopularityMetrics
from backend.permissions import IsOwnerOrReadOnly

CACHE_TIMEOUT = 60 * 30
logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    """Custom pagination settings."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProfileList(generics.ListAPIView):
    """List profiles with custom pagination."""

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        popularity_subquery = PopularityMetrics.objects.filter(user=OuterRef('user')).values('popularity_score')
        return Profile.objects.annotate(
            popularity_score=Subquery(popularity_subquery)
        ).order_by('-popularity_score')

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        """List profiles with caching."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a profile."""

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "user__id"
    lookup_url_kwarg = "user_id"

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a profile."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update a profile."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        """Save the updated profile."""
        serializer.save()
