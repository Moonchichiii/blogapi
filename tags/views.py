from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from .models import ProfileTag
from .serializers import ProfileTagSerializer

class CreateProfileTag(generics.CreateAPIView):
    serializer_class = ProfileTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            error_msg = str(e.detail[0]) if isinstance(e.detail, list) else str(e.detail)
            if "Invalid content type" in error_msg or "does not exist" in error_msg:
                return Response({"error": "Invalid content type for tagging."}, status=status.HTTP_400_BAD_REQUEST)
            elif "already tagged" in error_msg or "unique set" in error_msg:
                return Response({"error": "Duplicate tag: You have already tagged this user on this object."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"error": "Invalid content type for tagging."}, status=status.HTTP_400_BAD_REQUEST)