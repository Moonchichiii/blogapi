from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Follow
from .serializers import FollowSerializer
from profiles.models import Profile
from .signals import invalidate_follower_cache
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class FollowerDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("POST request received.")
        followed_id = request.data.get("followed")
        print(f"Followed ID: {followed_id}")
        
        if not followed_id or request.user.id == int(followed_id):
            logger.warning(f"User {request.user.id} tried to follow themselves or provided an invalid ID.")
            print("Invalid follow attempt.")
            return Response({
                "error": "You cannot follow yourself or the provided ID is invalid.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            followed_user = User.objects.get(id=followed_id)
        except User.DoesNotExist:
            logger.warning(f"User {request.user.id} tried to follow non-existent user {followed_id}.")
            return Response({
                "error": "The user you're trying to follow doesn't exist.",
                "type": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user, followed=followed_user
        )
        print(f"Follow object: {follow}, Created: {created}")
        
        if created:
            serializer = self.get_serializer(follow)
            
            logger.info(f"User {request.user.id} successfully followed user {followed_id}.")
            print("Follow successful.")
            return Response({
                "data": serializer.data,
                "message": "You have successfully followed the user.",
                "type": "success"
            }, status=status.HTTP_201_CREATED)
        
        logger.info(f"User {request.user.id} is already following user {followed_id}.")
        print("Already following.")
        return Response({
            "error": "You are already following this user.",
            "type": "error"
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        print("DELETE request received.")
        followed_id = request.data.get("followed")
        print(f"Followed ID: {followed_id}")
        if not followed_id:
            logger.warning(f"User {request.user.id} provided no followed ID for unfollowing.")
            print("No followed ID provided.")
            return Response({
                "error": "Followed user ID is required.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            follow = Follow.objects.get(follower=request.user, followed_id=followed_id)
            follow.delete()

            # Update follower count
            Profile.objects.filter(user_id=followed_id).update(
                follower_count=Follow.objects.filter(followed_id=followed_id).count()
            )

            logger.info(f"User {request.user.id} successfully unfollowed user {followed_id}.")
            print("Unfollow successful.")
            return Response({
                "message": "You have successfully unfollowed the user.",
                "type": "success"
            }, status=status.HTTP_200_OK)
        except Follow.DoesNotExist:
            logger.warning(f"User {request.user.id} attempted to unfollow user {followed_id} but was not following them.")
            print("Not following the user.")
            return Response({
                "error": "You are not following this user.",
                "type": "error"
            }, status=status.HTTP_400_BAD_REQUEST)
