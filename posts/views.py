from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post
from .serializers import PostSerializer, LimitedPostSerializer
from backend.permissions import IsOwnerOrReadOnly
from tags.models import ProfileTag


class PostList(generics.ListCreateAPIView):
    """
    API view to retrieve list of posts or create a new post.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_approved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = Post.objects.select_related('author').prefetch_related(
            'tags', 'comments__author', 'ratings__user'
        )
        author = self.request.query_params.get('author', None)
        is_approved = self.request.query_params.get('is_approved', None)
        search_query = self.request.query_params.get('search', None)

        if is_approved:
            queryset = queryset.filter(is_approved=is_approved)
        if search_query:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
        
        if self.request.user.is_authenticated:
            if author == 'current':
                queryset = queryset.filter(author=self.request.user)
            elif not (self.request.user.is_staff or self.request.user.is_superuser):
                queryset = queryset.filter(Q(is_approved=True) | Q(author=self.request.user))
        else:
            queryset = queryset.filter(is_approved=True)

        return queryset

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
    API view to retrieve, update or delete a post instance.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def check_object_permissions(self, request, obj):
        if request.method in ['PUT', 'PATCH'] and request.user.is_staff:
            return True
        return super().check_object_permissions(request, obj)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            serializer.save()
        elif user == serializer.instance.author:
            serializer.save(is_approved=False)
        else:
            raise permissions.PermissionDenied("You don't have permission to edit this post.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.author or request.user.is_superuser:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "You do not have permission to delete this post."}, status=status.HTTP_403_FORBIDDEN)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        content_type = ContentType.objects.get_for_model(Post)
        tags = ProfileTag.objects.filter(content_type=content_type, object_id=instance.id)
        tagged_users = [tag.tagged_user.profile_name for tag in tags]
        data['tagged_users'] = tagged_users
        return Response(data)


class ApprovePost(generics.UpdateAPIView):
    """
    API view to approve a post.
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(is_approved=True)


class DisapprovePost(APIView):
    """
    API view to disapprove a post.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        post = Post.objects.get(pk=pk)
        reason = request.data.get('reason')
        if not reason:
            return Response(
                {'error': 'Disapproval reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
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