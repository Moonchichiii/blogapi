from django.db import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .serializers import ProfileTagSerializer

class CreateProfileTag(generics.CreateAPIView):
    """API view to create a new profile tag."""
    serializer_class = ProfileTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                'data': serializer.data,
                'message': STANDARD_MESSAGES['TAG_CREATED_SUCCESS']['message'],
                'type': STANDARD_MESSAGES['TAG_CREATED_SUCCESS']['type']
            }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            raise ValidationError(STANDARD_MESSAGES['DUPLICATE_TAG']['message'])
        except ValidationError as e:
            return Response({
                'message': e.detail.get('message', 'Validation failed.'),
                'errors': e.detail,
                'type': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
