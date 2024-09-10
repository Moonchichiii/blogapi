from django.db.models import Avg, Count
from rest_framework import generics, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from backend.permissions import IsOwnerOrReadOnly
from tags.models import ProfileTag


class PostList(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'is_approved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            queryset = Post.objects.all()
        else:
            queryset = Post.objects.filter(is_approved=True)
        
        return queryset.annotate(
            average_rating=Avg('ratings__value'),
            total_ratings=Count('ratings')
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_update(self, serializer):
        if self.request.user.is_staff or self.request.user.is_superuser:
            serializer.save()
        elif self.request.user == serializer.instance.author:
            serializer.save(is_approved=False)
        else:
            raise permissions.PermissionDenied("You don't have permission to edit this post.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Get tagged users for this post
        content_type = ContentType.objects.get_for_model(Post)
        tags = ProfileTag.objects.filter(content_type=content_type, object_id=instance.id)
        tagged_users = [tag.tagged_user.profile_name for tag in tags]

        data['tagged_users'] = tagged_users
        return Response(data)

    def get_queryset(self):
        return Post.objects.annotate(
            average_rating=Avg('ratings__value'),
            total_ratings=Count('ratings')
        )

class ApprovePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(is_approved=True)