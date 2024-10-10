from django.utils.translation import gettext_lazy as _

MESSAGE_TYPES = {'SUCCESS': 'success', 'ERROR': 'error', 'WARNING': 'warning', 'INFO': 'info'}

STANDARD_MESSAGES = {
    'SUCCESS': {
        'REGISTRATION': _("Registration successful. Please check your email to activate your account."),
        'LOGIN': _("Login successful."),
        'LOGOUT': _("Logout successful."),
        'EMAIL_ACTIVATION': _("Your email has been successfully verified."),
        'PASSWORD_RESET': _("Password reset email sent. Please check your inbox."),
        'PASSWORD_CHANGE': _("Your password has been successfully changed."),
        'PROFILE_UPDATE': _("Your profile has been successfully updated."),
        '2FA_SETUP': _("Two-factor authentication has been set up successfully."),
    },
    'ERROR': {
        'INVALID_CREDENTIALS': _("Invalid credentials. Please try again."),
        'EMAIL_NOT_VERIFIED': _("Please verify your email before logging in."),
        'INVALID_TOKEN': _("Invalid or expired token. Please try again."),
        'PASSWORD_MISMATCH': _("The two password fields didn't match."),
        'EMAIL_EXISTS': _("A user with this email already exists."),
        'USERNAME_EXISTS': _("A user with this username already exists."),
        'INVALID_PASSWORD': _("This password is too weak. Please choose a stronger password."),
        '2FA_REQUIRED': _("Two-factor authentication is required for this account."),
        'ACCOUNT_NOT_ACTIVATED': _("Your account is not activated. Please check your email for the activation link."),
    },
}

MESSAGES = {
    'EMAIL_VERIFICATION_LINK': _("Please verify your email using this link: {verification_link}"),
    'PASSWORD_RESET_LINK': _("Use this link to reset your password: {reset_link}"),
}
