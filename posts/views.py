from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import generics, permissions, status, serializers
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from backend.permissions import IsOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import Post
from .serializers import PostSerializer, LimitedPostSerializer, PostListSerializer
from .messages import STANDARD_MESSAGES

CACHE_TIMEOUT_LONG = 60 * 15
CACHE_TIMEOUT_SHORT = 60 * 5
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

class PostCursorPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE

class PostPreviewList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = PostCursorPagination
    serializer_class = LimitedPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(is_approved=True).select_related('author').prefetch_related('tags').distinct()


    @method_decorator(cache_page(CACHE_TIMEOUT_LONG))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class PostList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PostCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_approved']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        return PostListSerializer if self.request.method == 'GET' else PostSerializer

    def get_queryset(self):
        queryset = Post.objects.select_related('author').prefetch_related(
            'tags', 'comments__author', 'ratings__user'
        ).annotate(
            comment_count=Count('comments', distinct=True),
            rating_count=Count('ratings', distinct=True)
        )

        if self.request.user.is_authenticated:
            if not (self.request.user.is_superuser or self.request.user.is_staff):
                queryset = queryset.filter(Q(author=self.request.user) | Q(is_approved=True))
        else:
            queryset = queryset.filter(is_approved=True)

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__profile_name__icontains=search_query)
            )

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            message = STANDARD_MESSAGES['POST_CREATED_SUCCESS']
            return Response({
                'data': serializer.data,
                'message': message['message'],
                'type': message['type']
            }, status=status.HTTP_201_CREATED, headers=headers)
        except serializers.ValidationError as e:
            error_message = e.detail.get('title', [])[0] if 'title' in e.detail else "Failed to create the post. Please check the provided data."
            return Response({
                'message': error_message,
                'type': "error",
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': "An unexpected error occurred.",
                'type': "error",
                'errors': {'detail': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save()

    @method_decorator(cache_page(CACHE_TIMEOUT_LONG))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(CACHE_TIMEOUT_SHORT))
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        message = STANDARD_MESSAGES['POSTS_RETRIEVED_SUCCESS']
        return Response({
            'results': response.data['results'],
            'next': response.data.get('next'),
            'previous': response.data.get('previous'),
            'count': response.data['count'],
            'message': message['message'],
            'type': message['type']
        })

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if not instance.is_approved and not (user == instance.author or user.is_staff or user.is_superuser):
            return Response({
                'message': "You do not have permission to view this post.",
                'type': "error"
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance, context={'request': request})
        data = serializer.data
        data['is_owner'] = user == instance.author
        data['tagged_users'] = [tag.tagged_user.profile_name for tag in instance.tags.select_related('tagged_user')]
        message = STANDARD_MESSAGES['POST_RETRIEVED_SUCCESS']
        return Response({
            'data': data,
            'message': message['message'],
            'type': message['type']
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            user = self.request.user
            if user.is_staff or user.is_superuser:
                self.perform_update(serializer)
                message = {
                    'message': "Your post has been updated successfully.",
                    'type': "success"
                }
            elif user == instance.author:
                self.perform_update(serializer)
                instance.is_approved = False
                instance.save()
                message = {
                    'message': "Your post has been updated and is pending approval.",
                    'type': "warning"
                }
            else:
                return Response({
                    'message': "You don't have permission to update this post.",
                    'type': "error"
                }, status=status.HTTP_403_FORBIDDEN)

            return Response({
                'data': serializer.data,
                'message': message['message'],
                'type': message['type']
            })
        except serializers.ValidationError as e:
            return Response({
                'message': "Failed to update the post. Please check your permissions or provided data.",
                'type': "error",
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': "An unexpected error occurred.",
                'type': "error",
                'errors': {'detail': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.author or request.user.is_superuser:
            self.perform_destroy(instance)
            return Response({
                'message': "Your post has been deleted successfully.",
                'type': "success"
            }, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({
                'message': "You do not have permission to delete this post.",
                'type': "error"
            }, status=status.HTTP_403_FORBIDDEN)

class ApprovePost(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                'data': serializer.data,
                'message': "The post has been approved successfully.",
                'type': "success"
            })
        except Exception as e:
            return Response({
                'message': "An unexpected error occurred.",
                'type': "error",
                'errors': {'detail': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_update(self, serializer):
        serializer.save(is_approved=True)

class DisapprovePost(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({
                'message': "The post you are trying to access does not exist.",
                'type': "error"
            }, status=status.HTTP_404_NOT_FOUND)

        reason = request.data.get('reason')
        if not reason:
            return Response({
                'message': "Disapproval reason is required.",
                'type': "error"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            post.is_approved = False
            post.save()

            send_mail(
                subject="Your post has been disapproved",
                message=f"Your post titled '{post.title}' has been disapproved for the following reason: {reason}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[post.author.email],
                fail_silently=False,
            )

            serializer = PostSerializer(post, context={'request': request})
            message = STANDARD_MESSAGES['POST_DISAPPROVED_SUCCESS']
            return Response({
                'data': serializer.data,
                'message': message['message'],
                'type': message['type']
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': "An unexpected error occurred.",
                'type': "error",
                'errors': {'detail': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
