from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import ProfileSerializer

# Create your views here.

class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile
