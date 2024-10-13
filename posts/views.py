import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.urls import reverse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.permissions import IsOwnerOrReadOnly
from .messages import STANDARD_MESSAGES
from .models import Post
from .serializers import LimitedPostSerializer, PostListSerializer, PostSerializer

logger = logging.getLogger(__name__)

CACHE_TIMEOUT_LONG = 60 * 15
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


class PostCursorPagination(PageNumberPagination):
    """Custom pagination class for paginating posts."""
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = MAX_PAGE_SIZE


class PostPreviewList(generics.ListAPIView):
    """List preview of approved posts for public access."""
    permission_classes = [permissions.AllowAny]
    pagination_class = PostCursorPagination
    serializer_class = LimitedPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    @method_decorator(cache_page(CACHE_TIMEOUT_LONG))
    def list(self, request, *args, **kwargs):
        """List cached and paginated approved posts."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Retrieve only approved posts for public view."""
        return (
            Post.objects.filter(is_approved=True)
            .select_related("author")
            .prefetch_related("tags")
            .distinct()
        )


class PostList(generics.ListCreateAPIView):
    """API view to list and create posts."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_approved"]
    search_fields = ["title", "content", "author__profile_name"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer class based on request method."""
        return PostListSerializer if self.request.method == "GET" else PostSerializer

    def get_queryset(self):
        """Return posts based on user permissions and search filters."""
        queryset = Post.objects.all().select_related("author").prefetch_related("tags", "ratings")
        user = self.request.user

        if user.is_authenticated and not (user.is_superuser or user.is_staff):
            queryset = queryset.filter(Q(author=user) | Q(is_approved=True))
        else:
            queryset = queryset.filter(is_approved=True)

        search_query = self.request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(author__profile_name__icontains=search_query)
            )
        return queryset.distinct()

    @method_decorator(cache_page(CACHE_TIMEOUT_LONG))
    def list(self, request, *args, **kwargs):
        """List cached and paginated posts."""
        response = super().list(request, *args, **kwargs)
        message = STANDARD_MESSAGES.get("POSTS_RETRIEVED_SUCCESS", {})
        response.data.update({
            "message": message.get("message", "Posts retrieved successfully."),
            "type": message.get("type", "success"),
        })
        return response

    def create(self, request, *args, **kwargs):
        """Handle post creation and return appropriate response."""
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        message = STANDARD_MESSAGES.get("POST_CREATED_SUCCESS", {})
        return Response({
            "data": serializer.data,
            "message": message.get("message", "Post created successfully."),
            "type": message.get("type", "success"),
        }, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Save the post with the current user as author."""
        serializer.save(author=self.request.user)


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    """API view to retrieve, update, or delete a post."""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def retrieve(self, request, *args, **kwargs):
        """Retrieve post details with appropriate permissions."""
        instance = self.get_object()
        user = request.user
        if not instance.is_approved and not (user == instance.author or user.is_staff or user.is_superuser):
            return Response(
                {
                    "message": "You do not have permission to view this post.",
                    "type": "error",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, context={"request": request})
        message = STANDARD_MESSAGES.get("POST_RETRIEVED_SUCCESS", {})
        return Response({
            "data": serializer.data,
            "message": message.get("message", "Post retrieved successfully."),
            "type": message.get("type", "success"),
        })

    def update(self, request, *args, **kwargs):
        """Handle post update requests with correct permissions."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        user = request.user
        if not (user == instance.author or user.is_staff or user.is_superuser):
            return Response(
                {"message": "You don't have permission to update this post.", "type": "error"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if user == instance.author:
            instance.is_approved = False
            instance.save(update_fields=["is_approved"])
            message = {
                "message": "Your post has been updated and is pending approval.",
                "type": "warning",
            }
        else:
            message = {
                "message": "Your post has been updated successfully.",
                "type": "success",
            }
        return Response({
            "data": serializer.data,
            "message": message["message"],
            "type": message["type"],
        })

    def destroy(self, request, *args, **kwargs):
        """Handle DELETE requests for posts."""
        instance = self.get_object()
        user = request.user
        if user == instance.author or user.is_superuser:
            self.perform_destroy(instance)
            return Response({
                "message": "Your post has been deleted successfully.",
                "type": "success",
            }, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({
                "message": "You do not have permission to delete this post.",
                "type": "error",
            }, status=status.HTTP_403_FORBIDDEN)


class ApprovePost(generics.UpdateAPIView):
    """API view to approve a post."""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        """Approve a post and return success message."""
        instance = self.get_object()
        instance.is_approved = True
        instance.save(update_fields=["is_approved"])
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "The post has been approved successfully.",
            "type": "success",
        })


class UnapprovedPostList(generics.ListAPIView):
    """List all unapproved posts for staff and superusers."""
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        """Retrieve unapproved posts."""
        return (
            Post.objects.filter(is_approved=False)
            .select_related("author")
            .prefetch_related("tags")
            .distinct()
        )


class DisapprovePost(APIView):
    """API view to disapprove a post."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        """Handle disapproval of a post with a reason."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({
                "message": "The post you are trying to access does not exist.",
                "type": "error",
            }, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get("reason")
        if not reason:
            return Response({
                "message": "Disapproval reason is required.",
                "type": "error",
            }, status=status.HTTP_400_BAD_REQUEST)

        post.is_approved = False
        post.save(update_fields=["is_approved"])

        send_mail(
            subject="Your post has been disapproved",
            message=f"Your post titled '{post.title}' has been disapproved for the following reason: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[post.author.email],
            fail_silently=False,
        )

        serializer = PostSerializer(post, context={"request": request})
        message = STANDARD_MESSAGES.get("POST_DISAPPROVED_SUCCESS", {})
        return Response({
            "data": serializer.data,
            "message": message.get("message", "Post disapproved successfully."),
            "type": message.get("type", "success"),
        }, status=status.HTTP_200_OK)