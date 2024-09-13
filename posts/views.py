from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post
from .serializers import PostSerializer
from backend.permissions import IsOwnerOrReadOnly
from tags.models import ProfileTag
from django.conf import settings


class PostList(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'is_approved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        # Check for an author query parameter, e.g., ?author=current
        author = self.request.query_params.get('author')
        if author == 'current' and self.request.user.is_authenticated:
            queryset = Post.objects.filter(author=self.request.user)
        elif self.request.user.is_staff or self.request.user.is_superuser:
            queryset = Post.objects.select_related('author').prefetch_related('tags').all()
        else:
            queryset = Post.objects.filter(is_approved=True).select_related('author').prefetch_related('tags')
        return queryset

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

        
        content_type = ContentType.objects.get_for_model(Post)
        tags = ProfileTag.objects.filter(content_type=content_type, object_id=instance.id)
        tagged_users = [tag.tagged_user.profile_name for tag in tags]

        data['tagged_users'] = tagged_users
        return Response(data)
class ApprovePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(is_approved=True)
        

class DisapprovePost(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        post = Post.objects.get(pk=pk)
        reason = request.data.get('reason')

        if not reason:
            return Response({'error': 'Disapproval reason is required'}, status=status.HTTP_400_BAD_REQUEST)

        post.is_approved = False
        post.save()

        author_email = post.author.email
        send_mail(
            subject="Your post has been disapproved",
            message=f"Your post titled '{post.title}' has been disapproved for the following reason: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[author_email],
            fail_silently=False,
        )

        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)