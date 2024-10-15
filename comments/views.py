from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from posts.models import Post
from .models import Comment
from .serializers import CommentSerializer
from backend.permissions import IsOwnerOrReadOnly

class CommentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = CommentPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs["post_id"], is_approved=True).select_related("author")

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        serializer.save(author=self.request.user, post=post)

    def create(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related("author", "post")
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

class ModerateComment(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        action = request.data.get("action")
        if action in ["approve", "disapprove"]:
            instance.is_approved = (action == "approve")
            instance.save()
            return Response({"status": f"Comment {action}d successfully"})
        return Response({"error": "Invalid action provided"}, status=status.HTTP_400_BAD_REQUEST)