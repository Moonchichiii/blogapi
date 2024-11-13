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
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from backend.permissions import (
    IsPostOwnerOrStaff,
    CanApprovePost,
    IsAdminUser
)
from comments.serializers import CommentSerializer
from .models import Post
from .serializers import PostListSerializer, PostSerializer
from .messages import STANDARD_MESSAGES

logger = logging.getLogger(__name__)

class PostCursorPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostList(generics.ListCreateAPIView):
    pagination_class = PostCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_approved"]
    search_fields = ["title", "content", "author__profile__profile_name"]
    ordering_fields = ["created_at", "updated_at", "average_rating"]
    ordering = ["-created_at"]
    permission_classes = [IsPostOwnerOrStaff]

    def get_serializer_class(self):
        if self.request.user.is_authenticated and self.request.query_params.get('detail') == 'true':
            return PostSerializer
        return PostListSerializer

    def get_queryset(self):
        queryset = Post.objects.select_related(
            "author", 
            "author__profile"
        ).prefetch_related(
            "tags", 
            "ratings",
            "comments"
        )
        
        user = self.request.user
        if not user.is_authenticated:
            return queryset.filter(is_approved=True)

        # Handle different user roles
        if user.has_permission_to(self.request, 'manage_content'):
            # Staff and admins can see all posts
            return queryset
        elif self.request.query_params.get("author") == "current":
            # Users can see their own posts
            return queryset.filter(author=user)
        else:
            # Users can see approved posts and their own posts
            return queryset.filter(Q(is_approved=True) | Q(author=user))

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.update({
            "message": STANDARD_MESSAGES.get("POSTS_RETRIEVED_SUCCESS"),
            "type": "success",
        })
        return response
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsPostOwnerOrStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def retrieve(self, request, *args, **kwargs):
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
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # If the author updates their post, it needs reapproval
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
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "message": "Post deleted successfully.",
            "type": "success",
        }, status=status.HTTP_204_NO_CONTENT)

class ApprovePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [CanApprovePost]

    def update(self, request, *args, **kwargs):
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
    serializer_class = PostListSerializer
    permission_classes = [CanApprovePost]

    def get_queryset(self):
        return Post.objects.filter(
            is_approved=False
        ).select_related("author").prefetch_related("tags").distinct()

class DisapprovePost(APIView):
    permission_classes = [CanApprovePost]

    def post(self, request, pk):
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
        
        # Send notification email
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
