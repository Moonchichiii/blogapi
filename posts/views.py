import logging
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from backend.permissions import IsOwnerOrAdmin, IsAdminOrSuperUser
from comments.serializers import CommentSerializer
from .models import Post
from .serializers import PostListSerializer, PostSerializer
from .messages import STANDARD_MESSAGES

logger = logging.getLogger(__name__)

class PostCursorPagination(PageNumberPagination):
    """Pagination class for posts."""
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostList(generics.ListCreateAPIView):
    """View for listing and creating posts."""
    pagination_class = PostCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_approved"]
    search_fields = ["title", "content", "author__profile__profile_name"]
    ordering_fields = ["created_at", "updated_at", "average_rating"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        """Return appropriate serializer class based on user authentication and query params."""
        if self.request.user.is_authenticated and self.request.query_params.get('detail') == 'true':
            return PostSerializer
        return PostListSerializer

    def get_queryset(self):
        """Return queryset based on user role and authentication."""
        queryset = Post.objects.select_related("author", "author__profile").prefetch_related("ratings", "comments")
        user = self.request.user
        if not user.is_authenticated:
            return queryset.filter(is_approved=True)
        if user.has_permission_to(self.request, 'manage_content'):
            return queryset
        elif self.request.query_params.get("author") == "current":
            return queryset.filter(author=user)
        return queryset.filter(Q(is_approved=True) | Q(author=user))

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        """List posts with caching."""
        response = super().list(request, *args, **kwargs)
        response.data.update({
            "message": STANDARD_MESSAGES.get("POSTS_RETRIEVED_SUCCESS"),
            "type": "success",
        })
        return response

    def perform_create(self, serializer):
        """Save the post with the current user as the author."""
        serializer.save(author=self.request.user)

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting a post."""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a post along with its comments."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data["comments"] = CommentSerializer(instance.comments.all(), many=True).data
        return Response({
            "data": data,
            "message": STANDARD_MESSAGES.get("POST_RETRIEVED_SUCCESS"),
            "type": "success",
        })

    def update(self, request, *args, **kwargs):
        """Update a post and handle reapproval if necessary."""
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        if request.user == instance.author and not request.user.has_permission_to(request, 'approve_posts'):
            instance.is_approved = False
            instance.save(update_fields=["is_approved"])
        self.perform_update(serializer)
        return Response({
            "data": serializer.data,
            "message": "Your post has been updated and is pending approval." if not instance.is_approved else "Post updated successfully.",
            "type": "warning" if not instance.is_approved else "success",
        })

    def destroy(self, request, *args, **kwargs):
        """Delete a post."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "message": "Post deleted successfully.",
            "type": "success",
        }, status=status.HTTP_204_NO_CONTENT)

class ApprovePost(generics.UpdateAPIView):
    """View for approving a post."""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAdminOrSuperUser]

    def update(self, request, *args, **kwargs):
        """Approve a post."""
        instance = self.get_object()
        instance.is_approved = True
        instance.save(update_fields=["is_approved"])
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Post approved successfully.",
            "type": "success",
        })


class UnapprovedPostList(generics.ListAPIView):
    """View for listing unapproved posts."""
    serializer_class = PostListSerializer
    permission_classes = [IsAdminOrSuperUser]

    def get_queryset(self):
        """Return queryset of unapproved posts."""
        return Post.objects.filter(is_approved=False).select_related("author").distinct()


class DisapprovePost(APIView):
    """View for disapproving a post."""
    permission_classes = [IsAdminOrSuperUser]

    def post(self, request, pk):
        """Disapprove a post and send notification email."""
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({
                "message": "Post not found.",
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
            message=f"Your post '{post.title}' has been disapproved.\nReason: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[post.author.email],
            fail_silently=False,
        )
        serializer = PostSerializer(post, context={"request": request})
        return Response({
            "data": serializer.data,
            "message": STANDARD_MESSAGES.get("POST_DISAPPROVED_SUCCESS"),
            "type": "success",
        })

