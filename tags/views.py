from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import ProfileTagSerializer

class CreateProfileTagView(generics.CreateAPIView):
    serializer_class = ProfileTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(tagger=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {'message': 'Tag created successfully', 'data': serializer.data}, 
            status=status.HTTP_201_CREATED
        )
