from django.conf import settings
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import generics, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post
from .serializers import PostSerializer, LimitedPostSerializer
from backend.permissions import IsOwnerOrReadOnly
from tags.models import ProfileTag


class PostList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_approved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = Post.objects.select_related('author').prefetch_related(
            'tags',
            'comments__author',
            'ratings__user'
        )
        author = self.request.query_params.get('author', None)

        if self.request.user.is_authenticated:
            if author == 'current':
                return queryset.filter(author=self.request.user)
            elif self.request.user.is_staff or self.request.user.is_superuser:
                return queryset
            else:
                return queryset.filter(Q(is_approved=True) | Q(author=self.request.user))
        else:
            return queryset.filter(is_approved=True)

    def get_serializer_class(self):
        if not self.request.user.is_authenticated:
            return LimitedPostSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a specific post.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        """
        Custom update behavior based on user permissions.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            serializer.save()
        elif user == serializer.instance.author:
            serializer.save(is_approved=False)
        else:
            raise permissions.PermissionDenied("You don't have permission to edit this post.")

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves a specific post with tagged users.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        content_type = ContentType.objects.get_for_model(Post)
        tags = ProfileTag.objects.filter(content_type=content_type, object_id=instance.id)
        tagged_users = [tag.tagged_user.profile_name for tag in tags]
        data['tagged_users'] = tagged_users

        return Response(data)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)  


class ApprovePost(generics.UpdateAPIView):
    """
    View to approve a specific post, restricted to admin users.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        """
        Marks a post as approved.
        """
        serializer.save(is_approved=True)


class DisapprovePost(APIView):
    """
    View to disapprove a specific post, restricted to admin users.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        """
        Disapproves the post and notifies the author via email.
        """
        post = Post.objects.get(pk=pk)
        reason = request.data.get('reason')

        if not reason:
            return Response({'error': 'Disapproval reason is required'}, status=status.HTTP_400_BAD_REQUEST)

        post.is_approved = False
        post.save()

        send_mail(
            subject="Your post has been disapproved",
            message=f"Your post titled '{post.title}' has been disapproved for the following reason: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[post.author.email],
            fail_silently=False,
        )

        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)
