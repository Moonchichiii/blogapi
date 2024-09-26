from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Prefetch
from backend.permissions import IsOwnerOrReadOnly
from posts.models import Post
from .models import Comment
from .serializers import CommentSerializer

class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        try:
            post = Post.objects.prefetch_related(
                Prefetch(
                    'comments',
                    queryset=Comment.objects.select_related('author'),
                    to_attr='prefetched_comments'
                )
            ).get(pk=post_id)
        except Post.DoesNotExist as exc:
            raise Http404("Post does not exist") from exc
        
        if not self.request.user.is_authenticated:
            return []
        
        return post.prefetched_comments

    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist as exc:
            raise Http404("Post does not exist") from exc
        serializer.save(author=self.request.user, post=post)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required to view comments."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required to view comments."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)