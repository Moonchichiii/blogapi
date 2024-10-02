from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import generics, permissions, serializers, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

from .messages import STANDARD_MESSAGES
from .models import Post
from .serializers import PostSerializer, LimitedPostSerializer, PostListSerializer
from backend.permissions import IsOwnerOrReadOnly
from tags.models import ProfileTag

class PostCursorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_approved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Optimize query fetching with related fields to minimize queries."""
        queryset = Post.objects.select_related('author').prefetch_related(
            'tags', 'comments__author', 'ratings__user'
        )
        author = self.request.query_params.get('author', None)
        search_query = self.request.query_params.get('search', None)

        if self.request.user.is_authenticated:
            if author == 'current':
                queryset = queryset.filter(author=self.request.user)
            elif not (self.request.user.is_staff or self.request.user.is_superuser):
                queryset = queryset.filter(Q(is_approved=True) | Q(author=self.request.user))
        else:
            queryset = queryset.filter(is_approved=True)

        if search_query:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostListSerializer
        return PostSerializer if self.request.user.is_authenticated else LimitedPostSerializer

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if hasattr(self, 'paginator') and self.paginator:
            count = self.paginator.page.paginator.count
        else:
            count = len(response.data.get('results', []))

        response_data = {
            'results': response.data.get('results', []),
            'count': count,
            'message': STANDARD_MESSAGES['POSTS_RETRIEVED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['POSTS_RETRIEVED_SUCCESS']['type']
        }
        return Response(response_data)

    def perform_create(self, serializer):
        try:
            post = serializer.save(author=self.request.user)
            return Response({
                'data': PostSerializer(post).data,
                'message': STANDARD_MESSAGES['POST_CREATED_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['POST_CREATED_SUCCESS']['type']
            }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            raise serializers.ValidationError({
                'message': STANDARD_MESSAGES['POST_DUPLICATE_TITLE']['message'],
                'type': STANDARD_MESSAGES['POST_DUPLICATE_TITLE']['type']
            })

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def check_object_permissions(self, request, obj):
        """Custom object permission check to allow staff updates."""
        if request.method in ['PUT', 'PATCH'] and request.user.is_staff:
            return True
        return super().check_object_permissions(request, obj)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Staff or superusers can approve the post directly
            serializer.save()
            return Response({
                'message': STANDARD_MESSAGES['POST_UPDATED_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['POST_UPDATED_SUCCESS']['type']
            })
        elif user == serializer.instance.author:
            # Non-staff authors update but their post needs approval
            serializer.save(is_approved=False)
            return Response({
                'message': STANDARD_MESSAGES['POST_UPDATED_PENDING_APPROVAL']['message'],
                'type': STANDARD_MESSAGES['POST_UPDATED_PENDING_APPROVAL']['type']
            })
        else:
            return Response({
                'message': STANDARD_MESSAGES['POST_DELETE_PERMISSION_DENIED']['message'],
                'type': STANDARD_MESSAGES['POST_DELETE_PERMISSION_DENIED']['type']
            }, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.author or request.user.is_superuser:
            self.perform_destroy(instance)
            return Response({
                'message': STANDARD_MESSAGES['POST_DELETED_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['POST_DELETED_SUCCESS']['type']
            }, status=status.HTTP_204_NO_CONTENT)
        return Response({
            'message': STANDARD_MESSAGES['POST_DELETE_PERMISSION_DENIED']['message'],
            'type': STANDARD_MESSAGES['POST_DELETE_PERMISSION_DENIED']['type']
        }, status=status.HTTP_403_FORBIDDEN)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        content_type = ContentType.objects.get_for_model(Post)
        tags = ProfileTag.objects.filter(content_type=content_type, object_id=instance.id)
        tagged_users = [tag.tagged_user.profile_name for tag in tags]
        data['tagged_users'] = tagged_users

        return Response({
            'data': data,
            'message': STANDARD_MESSAGES['POST_RETRIEVED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['POST_RETRIEVED_SUCCESS']['type']
        })

class ApprovePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(is_approved=True)
        return Response({
            'message': STANDARD_MESSAGES['POST_APPROVED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['POST_APPROVED_SUCCESS']['type']
        })

class DisapprovePost(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({
                'message': STANDARD_MESSAGES['POST_NOT_FOUND']['message'],
                'type': STANDARD_MESSAGES['POST_NOT_FOUND']['type']
            }, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason')
        if not reason:
            return Response({
                'message': STANDARD_MESSAGES['POST_DISAPPROVE_REASON_REQUIRED']['message'],
                'type': STANDARD_MESSAGES['POST_DISAPPROVE_REASON_REQUIRED']['type']
            }, status=status.HTTP_400_BAD_REQUEST)

        post.is_approved = False
        post.save()

        # Notify the post author via email
        send_mail(
            subject="Your post has been disapproved",
            message=f"Your post titled '{post.title}' has been disapproved for the following reason: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[post.author.email],
            fail_silently=False,
        )

        serializer = PostSerializer(post)
        return Response({
            'data': serializer.data,
            'message': STANDARD_MESSAGES['POST_DISAPPROVED_SUCCESS']['message'],
            'type': STANDARD_MESSAGES['POST_DISAPPROVED_SUCCESS']['type']
        }, status=status.HTTP_200_OK)
