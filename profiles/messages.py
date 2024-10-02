from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
}

STANDARD_MESSAGES = {
    # Success Messages
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
    'PROFILE_FOLLOWED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Profile followed successfully."),
    },
    'PROFILE_UNFOLLOWED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Profile unfollowed successfully."),
    },

    # Error Messages
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

    # Warning Messages
    'PROFILE_INCOMPLETE_WARNING': {
        'type': MESSAGE_TYPES['WARNING'],
        'message': _("Your profile is incomplete. Please update your profile."),
    },

    # Information Messages
    'PROFILE_PUBLIC_INFO': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("This profile is public and visible to everyone."),
    },
    'PROFILE_PRIVATE_INFO': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("This profile is private and only visible to followers."),
    },
}
