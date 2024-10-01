from rest_framework import generics, permissions, status
from rest_framework.response import Response
from posts.models import Post
from .models import Rating
from .serializers import RatingSerializer


class CreateUpdateRating(generics.CreateAPIView):
    """
    API view to create or update a rating for a post.
    """
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Handle the creation or update of a rating.
        """
        user = request.user
        post_id = request.data.get('post')

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            instance = Rating.objects.get(user=user, post=post)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            status_code = status.HTTP_200_OK
        except Rating.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            status_code = status.HTTP_201_CREATED

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status_code, headers=headers)

    def perform_create(self, serializer):
        """
        Save the rating instance with the current user.
        """
        serializer.save(user=self.request.user)