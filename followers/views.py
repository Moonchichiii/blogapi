from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Follow
from .serializers import FollowSerializer
from .messages import STANDARD_MESSAGES


class FollowerListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(followed_id=user_id)


class FollowUnfollowView(generics.CreateAPIView, generics.DestroyAPIView):
    """
    API view to handle following and unfollowing users.
    """
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Handle the follow action.
        """
        followed_id = request.data.get('followed')
        if not followed_id:
            return Response({
                'error': "Followed user ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        if request.user.id == int(followed_id):
            return Response({
                'error': STANDARD_MESSAGES['CANNOT_FOLLOW_SELF']['message'],
            }, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(
            follower=request.user, followed_id=followed_id
        )
        if created:
            serializer = FollowSerializer(follow)
            return Response({
                'data': serializer.data,
                'message': STANDARD_MESSAGES['FOLLOW_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['FOLLOW_SUCCESS']['type']
            }, status=status.HTTP_201_CREATED)
        return Response({
            'error': STANDARD_MESSAGES['ALREADY_FOLLOWING']['message'],
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Handle the unfollow action.
        """
        followed_id = request.data.get('followed')
        if not followed_id:
            return Response({
                'error': "Followed user ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            follow = Follow.objects.get(
                follower=request.user, followed_id=followed_id
            )
            follow.delete()
            return Response({
                'message': STANDARD_MESSAGES['UNFOLLOW_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['UNFOLLOW_SUCCESS']['type']
            }, status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            return Response({
                'error': STANDARD_MESSAGES['NOT_FOLLOWING']['message'],
            }, status=status.HTTP_400_BAD_REQUEST)
