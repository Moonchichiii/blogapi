from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
}

STANDARD_MESSAGES = {
    # Success Messages
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
    'EMAIL_UPDATE_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your email has been successfully updated."),
    },
    'ACCOUNT_DELETION_SUCCESS': {
        'type': MESSAGE_TYPES['SUCCESS'],
        'message': _("Your account has been successfully deleted."),
    },

    # Error Messages
    'INVALID_CREDENTIALS': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Invalid credentials. Please check your email and password."),
    },
    'USER_NOT_FOUND': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("User not found. Please try again."),
    },
    'ACCOUNT_NOT_ACTIVATED': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Your account is not activated. Please check your email for the activation link."),
    },
    'INVALID_TOKEN': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("Invalid or expired token."),
    },
    
    # Password Validation Errors
    'PASSWORD_TOO_SHORT': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("This password must contain at least 8 characters."),
    },
    'PASSWORD_NO_SYMBOL': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("The password must contain at least one symbol: !@#$%^&*(),.?\":{}|<>"),
    },
    'PASSWORD_NO_UPPER': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("The password must contain at least one uppercase letter, A-Z."),
    },
    'PASSWORD_NO_NUMBER': {
        'type': MESSAGE_TYPES['ERROR'],
        'message': _("The password must contain at least one number, 0-9."),
    },
}
