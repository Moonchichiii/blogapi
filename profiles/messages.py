from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

# Define message types
MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
}

# Define standard messages for profile operations
STANDARD_MESSAGES = {
    'PROFILE_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Profile retrieved successfully."),
    },
    'PROFILE_UPDATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Profile updated successfully."),
    },
    'PROFILE_IMAGE_UPDATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Profile image updated successfully."),
    },
    'PROFILE_NOT_FOUND': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Profile not found. Please try again."),
    },
    'PROFILE_UPDATE_FAILED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Failed to update profile. Please check the provided data."),
    },
    'PROFILE_IMAGE_SIZE_LIMIT_EXCEEDED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Profile image size exceeds the 2MB limit."),
    },
    'CANNOT_FOLLOW_OWN_PROFILE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You cannot follow your own profile."),
    },
    'ALREADY_FOLLOWING_PROFILE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You are already following this profile."),
    },
    'NOT_FOLLOWING_PROFILE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You are not following this profile."),
    },
    'UNAUTHORIZED_PROFILE_UPDATE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You are not authorized to update this profile."),
    },
    'INVALID_BIO_LENGTH': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Bio length should not exceed 500 characters."),
    },
    'PROFILE_INCOMPLETE_WARNING': {
        'type': MESSAGE_TYPES['WARNING'],
        'message': _("Your profile is incomplete. Please update your profile."),
    },
    'PROFILE_PUBLIC_INFO': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("This profile is public and visible to everyone."),
    },
    'PROFILE_PRIVATE_INFO': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("This profile is private and only visible to followers."),
    },
}

def profile_success_response(message_key: str, data: dict = None):
    """
    Helper function to create a success response for profile-related operations.
    
    Args:
        message_key (str): The key from the STANDARD_MESSAGES dict.
        data (dict): The data to include in the response.

    Returns:
        Response: A formatted success response.
    """
    message = STANDARD_MESSAGES.get(message_key, {})
    response_data = {
        'message': message.get('message', 'Action completed successfully.'),
        'type': message.get('type', 'success')
    }
    if data:
        response_data['data'] = data
    return Response(response_data)
