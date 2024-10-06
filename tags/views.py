from django.db import IntegrityError
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .messages import STANDARD_MESSAGES
from .serializers import ProfileTagSerializer

class CreateProfileTag(generics.CreateAPIView):
    """
    API view to create a new profile tag.
    """
    serializer_class = ProfileTagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Handle the creation of a new profile tag.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            message = STANDARD_MESSAGES['TAG_CREATED_SUCCESS']
            return Response({
                'data': serializer.data,
                'message': message['message'],
                'type': message['type']
            }, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError:
            raise ValidationError({
                'message': STANDARD_MESSAGES['DUPLICATE_TAG']['message']
            })
        except serializers.ValidationError as e:
            error_message = e.detail.get('message', [STANDARD_MESSAGES['INVALID_CONTENT_TYPE']['message']])[0]
            return Response({
                'error': error_message,
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
