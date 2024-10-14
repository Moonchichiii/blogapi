from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from posts.models import Post
from .models import Comment
from .serializers import CommentSerializer


class CommentPagination(PageNumberPagination):
    """Pagination settings for comments."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CommentList(generics.ListCreateAPIView):
    """List and create comments for a specific post."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CommentPagination

    def get_queryset(self):
        """Return comments for the specified post."""
        return Comment.objects.filter(post=self.kwargs["post_id"]).select_related(
            "author"
        )

    def perform_create(self, serializer):
        """Save the comment with the current user as the author."""
        try:
            post = Post.objects.get(pk=self.kwargs["post_id"])
            serializer.save(author=self.request.user, post=post)
            return Response(
                {"message": "Comment created successfully.", "type": "success"},
                status=status.HTTP_201_CREATED,
            )
        except Post.DoesNotExist:
            return Response(
                {"message": "Post not found.", "type": "error"},
                status=status.HTTP_404_NOT_FOUND,
            )


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a comment."""

    queryset = Comment.objects.select_related("author", "post")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ModerateComment(generics.UpdateAPIView):
    """Approve or disapprove a comment."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        """Update the approval status of a comment."""
        instance = self.get_object()
        action = request.data.get("action")
        if action == "approve":
            instance.is_approved = True
            instance.save()
            return Response(
                {"message": "Comment approved successfully.", "type": "success"},
                status=status.HTTP_200_OK,
            )
        elif action == "disapprove":
            instance.is_approved = False
            instance.save()
            return Response(
                {"message": "Comment disapproved successfully.", "type": "success"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Invalid action provided.", "type": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
