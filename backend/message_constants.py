from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
}

STANDARD_MESSAGES = {
    'REGISTRATION_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Registration successful. Please check your email to activate your account."),
    },
    'LOGIN_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Login successful."),
    },
    'LOGOUT_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Logout successful."),
    },
    'PASSWORD_RESET_REQUEST': {
        'type': MESSAGE_TYPES['INFO'],
        'message': _("If an account exists with this email, a password reset link has been sent."),
    },
    'PASSWORD_RESET_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your password has been successfully reset."),
    },
    'EMAIL_UPDATE_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your email has been successfully updated."),
    },
    'PROFILE_UPDATE_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your profile has been successfully updated."),
    },
    'ACCOUNT_DELETION_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your account has been successfully deleted."),
    },
    'GENERIC_ERROR': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("An error occurred. Please try again."),
    },
}