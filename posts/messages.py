from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
}

STANDARD_MESSAGES = {
    # Success Messages
    'POST_CREATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your post has been created successfully."),
    },
    'POST_UPDATED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your post has been updated successfully."),
    },
    'POST_DELETED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your post has been deleted successfully."),
    },
    'POST_APPROVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("The post has been approved successfully."),
    },
    'POST_LIST_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Posts list retrieved successfully."),
    },
    'POST_DISAPPROVED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("The post has been disapproved and the author has been notified."),
    },
    'RATING_ADDED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Thank you! Your rating has been submitted."),
    },
    'COMMENT_ADDED_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your comment has been added to the post."),
    },

    # Error Messages
    'POST_NOT_FOUND': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("The post you are trying to access does not exist."),
    },
    'POST_CREATION_FAILED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Failed to create the post. Please check the provided data."),
    },
    'POST_UPDATE_FAILED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Failed to update the post. Please check your permissions or provided data."),
    },
    'POST_DELETE_FAILED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You do not have permission to delete this post."),
    },
    'POST_APPROVAL_FAILED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You do not have permission to approve this post."),
    },
    'POST_UPDATED_PENDING_APPROVAL': {
        'type': MESSAGE_TYPES['WARNING'],
        'message': _("Your post has been updated and is pending approval."),
    },
    'POST_DISAPPROVE_REASON_REQUIRED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Disapproval reason is required."),
    },
    'INVALID_RATING': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Invalid rating. Please provide a rating between 1 and 5."),
    },
    'POST_TAGS_DUPLICATE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Duplicate tags are not allowed."),
    },
    'DUPLICATE_TAG_ERROR': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Duplicate tags are not allowed."),
    },
    'IMAGE_FORMAT_INVALID': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Invalid image format. Only JPG, JPEG, PNG, and GIF formats are allowed."),
    },
    'POST_UPDATE_PERMISSION_DENIED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("You don't have permission to update this post."),
    },
    'POST_DUPLICATE_TITLE': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("A post with this title already exists. Please choose a different title."),
    },

    # Warning Messages
    'POST_PENDING_APPROVAL': {
        'type': MESSAGE_TYPES['WARNING'],
        'message': _("Your post is pending approval and will be reviewed soon."),
    },

    # Information Messages
    'POSTS_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("Posts have been retrieved successfully."),
    },
    'POST_RETRIEVED_SUCCESS': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("Post has been retrieved successfully."),
    },
    'RATING_ALREADY_SUBMITTED': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("You have already submitted a rating for this post."),
    },
}
