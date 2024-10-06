from django.utils.translation import gettext_lazy as _

# Define message types for standard messages
MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
}

# Standard messages used throughout the application
STANDARD_MESSAGES = {
    'TAG_CREATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Tag created successfully."),
    },
    'INVALID_CONTENT_TYPE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Invalid content type for tagging."),
    },
    'DUPLICATE_TAG': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Duplicate tag: You have already tagged this user on this object."),
    },
    'CANNOT_TAG_SELF': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You cannot tag yourself."),
    },
}
