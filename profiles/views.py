from django.db.models import Count, Avg
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import ProfileSerializer
from .models import Profile
from backend.permissions import IsOwnerOrReadOnly


class CurrentUserProfileView(APIView):
    """
    View to retrieve and update the current user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve the current user's profile with additional annotations.
        """
        profile = Profile.objects.filter(user=request.user).annotate(
            follower_count=Count('user__followers'),
            following_count=Count('user__following'),
            avg_post_rating=Avg('user__posts__average_rating'),
            comment_count=Count('user__comments'),
            tag_count=Count('user__tags')
        ).first()
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        """
        Update the current user's profile.
        """
        serializer = ProfileSerializer(request.user.profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ProfilePagination(PageNumberPagination):
    """
    Custom pagination class for profiles.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProfileList(generics.ListAPIView):
    """
    View to list all profiles with pagination and caching.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    pagination_class = ProfilePagination

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        """
        List profiles with caching.
        """
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Annotate profiles with follower and following counts, and order by popularity.
        """
        return Profile.objects.annotate(
            follower_count=Count('user__followers'),
            following_count=Count('user__following')
        ).order_by('-popularity_score', '-follower_count')


class ProfileView(generics.RetrieveAPIView):
    """
    View to retrieve a profile by user ID.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'


class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = ProfileSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(self.request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)