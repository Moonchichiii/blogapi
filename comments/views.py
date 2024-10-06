from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from backend.permissions import IsOwnerOrReadOnly
from posts.models import Post
from .messages import STANDARD_MESSAGES
from .models import Comment
from .serializers import CommentSerializer


class CommentPagination(LimitOffsetPagination):
    """Pagination settings for comments."""
    default_limit: int = 10
    max_limit: int = 50


class CommentList(generics.ListCreateAPIView):
    """
    View to list all comments for a specific post and create a new comment.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CommentPagination

    def get_queryset(self) -> list[Comment]:
        """
        Get the queryset of comments for a specific post.
        """
        post_id = self.kwargs['post_id']
        try:
            post = Post.objects.prefetch_related(
                Prefetch(
                    'comments',
                    queryset=Comment.objects.select_related('author').order_by('-created_at'),
                    to_attr='prefetched_comments'
                )
            ).get(pk=post_id)
        except Post.DoesNotExist as exc:
            raise Http404(STANDARD_MESSAGES['POST_NOT_FOUND']['message']) from exc
        return post.prefetched_comments

    def list(self, request, *args, **kwargs) -> Response:
        """
        List all comments for a specific post with pagination.
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)

        if page is not None:
            paginated_response = self.get_paginated_response(serializer.data)
            paginated_response.data['message'] = STANDARD_MESSAGES['COMMENTS_RETRIEVED_SUCCESS']['message']
            paginated_response.data['type'] = STANDARD_MESSAGES['COMMENTS_RETRIEVED_SUCCESS']['type']
            return paginated_response

        return Response({
            'data': serializer.data,
            'message': STANDARD_MESSAGES['COMMENTS_RETRIEVED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['COMMENTS_RETRIEVED_SUCCESS']['type']
        })

    def create(self, request, *args, **kwargs) -> Response:
        """
        Create a new comment for a specific post.
        """
        post_id = self.kwargs['post_id']
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist as exc:
            raise Http404(STANDARD_MESSAGES['POST_NOT_FOUND']['message']) from exc

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user, post=post)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'data': serializer.data,
            'message': STANDARD_MESSAGES['COMMENT_CREATED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['COMMENT_CREATED_SUCCESS']['type']
        }, status=status.HTTP_201_CREATED, headers=headers)


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a specific comment.
    """
    queryset = Comment.objects.select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        Retrieve a specific comment with a success message.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'data': serializer.data,
            'message': STANDARD_MESSAGES['COMMENT_RETRIEVED_SUCCESS']['message']
        })
