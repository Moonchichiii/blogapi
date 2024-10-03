from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
}

STANDARD_MESSAGES = {
    'POST_CREATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your post has been created successfully."),
    },
    'POST_DISAPPROVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("The post has been disapproved and the author has been notified."),
    },
    'POSTS_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("Posts list retrieved successfully."),
    },
    'POST_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("Post has been retrieved successfully."),
    },
}
