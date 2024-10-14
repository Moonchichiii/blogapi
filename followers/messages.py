from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    "SUCCESS": "success",
    "ERROR": "error",
    "INFO": "info",
}

STANDARD_MESSAGES = {
    "FOLLOW_SUCCESS": {
        "type": MESSAGE_TYPES["SUCCESS"],
        "message": _("You have successfully followed the user."),
    },
    "UNFOLLOW_SUCCESS": {
        "type": MESSAGE_TYPES["SUCCESS"],
        "message": _("You have successfully unfollowed the user."),
    },
    "CANNOT_FOLLOW_SELF": {
        "type": MESSAGE_TYPES["ERROR"],
        "message": _("You cannot follow yourself."),
    },
    "ALREADY_FOLLOWING": {
        "type": MESSAGE_TYPES["ERROR"],
        "message": _("You are already following this user."),
    },
    "NOT_FOLLOWING": {
        "type": MESSAGE_TYPES["ERROR"],
        "message": _("You are not following this user."),
    },
}
