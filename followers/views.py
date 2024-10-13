from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Follow
from .serializers import FollowSerializer



from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Follow
from .serializers import FollowSerializer

class FollowerListView(generics.ListAPIView):
    """List followers of a user."""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(followed_id=user_id).select_related('follower', 'follower__profile')

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class FollowUnfollowView(generics.GenericAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Handle following a user."""
        followed_id = request.data.get('followed')
        if not followed_id or request.user.id == int(followed_id):
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or retrieve the follow instance
        follow, created = Follow.objects.get_or_create(follower=request.user, followed_id=followed_id)
        if created:
            serializer = self.get_serializer(follow)
            return Response({
                'data': serializer.data,
                'message': 'You have successfully followed the user.',
                'type': 'success'
            }, status=status.HTTP_201_CREATED)

        return Response({'error': 'You are already following this user.'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Handle unfollowing a user."""
        followed_id = request.data.get('followed')
        if not followed_id:
            return Response({'error': "Followed user ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to delete the follow instance
        try:
            follow = Follow.objects.get(follower=request.user, followed_id=followed_id)
            follow.delete()
            return Response({
                'message': 'You have successfully unfollowed the user.',
                'type': 'success'
            }, status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            return Response({'error': 'You are not following this user.'}, status=status.HTTP_400_BAD_REQUEST)
