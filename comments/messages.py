from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    "SUCCESS": "success",
    "ERROR": "error",
    "INFO": "info",
}

COMMENT_MESSAGES = {
    "COMMENT_RETRIEVED_SUCCESS": {
        "type": MESSAGE_TYPES["SUCCESS"],
        "message": _("Comment retrieved successfully."),
    },
    "COMMENT_CREATED_SUCCESS": {
        "type": MESSAGE_TYPES["SUCCESS"],
        "message": _("Comment added successfully!"),
    },
    "COMMENT_UPDATED_SUCCESS": {
        "type": MESSAGE_TYPES["SUCCESS"],
        "message": _("Comment updated successfully."),
    },
    "COMMENT_DELETED_SUCCESS": {
        "type": MESSAGE_TYPES["SUCCESS"],
        "message": _("Comment deleted successfully."),
    },
}
