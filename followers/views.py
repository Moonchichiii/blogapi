from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import F, Avg, Count
from .models import Follow
from .serializers import FollowSerializer
import logging

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 60 * 5

class CustomPagination(PageNumberPagination):
    """Custom pagination settings."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class FollowerListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "data": serializer.data,
                "message": "Followers retrieved successfully",
                "type": "success"
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Followers retrieved successfully",
            "type": "success"
        })

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        order_by = self.request.query_params.get('order_by', 'created_at')
        queryset = Follow.objects.filter(followed_id=user_id).select_related(
            "follower", "follower__profile"
        ).annotate(
            average_rating=Avg('follower__posts__average_rating'),
            post_count=Count('follower__posts')
        )
        if order_by == 'popularity':
            return queryset.order_by(F("follower__profile__popularity_score").desc(nulls_last=True))
        return queryset.order_by('-created_at')

class FollowerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Handle follow, unfollow, and retrieve specific follow details."""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        followed_id = request.data.get("followed")
        if not followed_id or request.user.id == int(followed_id):
            logger.warning(f"User {request.user.id} tried to follow themselves or provided an invalid ID.")
            return Response({
                "error": "You cannot follow yourself or the provided ID is invalid.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        follow, created = Follow.objects.get_or_create(
            follower=request.user, followed_id=followed_id
        )
        if created:
            serializer = self.get_serializer(follow)
            logger.info(f"User {request.user.id} successfully followed user {followed_id}.")
            return Response({
                "data": serializer.data,
                "message": "You have successfully followed the user.",
                "type": "success"
            }, status=status.HTTP_201_CREATED)
        logger.info(f"User {request.user.id} is already following user {followed_id}.")
        return Response({
            "error": "You are already following this user.",
            "type": "error"
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        followed_id = request.data.get("followed")
        if not followed_id:
            logger.warning(f"User {request.user.id} provided no followed ID for unfollowing.")
            return Response({
                "error": "Followed user ID is required.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            follow = Follow.objects.get(follower=request.user, followed_id=followed_id)
            follow.delete()
            logger.info(f"User {request.user.id} successfully unfollowed user {followed_id}.")
            return Response({
                "message": "You have successfully unfollowed the user.",
                "type": "success"
            }, status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            logger.warning(f"User {request.user.id} attempted to unfollow user {followed_id} but was not following them.")
            return Response({
                "error": "You are not following this user.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
