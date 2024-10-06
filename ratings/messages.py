from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
}

STANDARD_MESSAGES = {
    'RATING_CREATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Rating created successfully."),
    },
    'RATING_UPDATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Rating updated successfully."),
    },
    'POST_NOT_FOUND': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("The post you are trying to rate does not exist."),
    },
    'POST_NOT_APPROVED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You cannot rate an unapproved post."),
    },
    'INVALID_RATING_VALUE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Rating value must be between 1 and 5."),
    },
}