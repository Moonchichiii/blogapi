from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'INFO': 'info',
}

STANDARD_MESSAGES = {
    'POST_NOT_FOUND': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("The post you are trying to access does not exist."),
    },
    'AUTHENTICATION_REQUIRED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Authentication required to view comments."),
    },
    'COMMENTS_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Comments retrieved successfully."),
    },
    'COMMENT_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Comment retrieved successfully."),
    },
}
