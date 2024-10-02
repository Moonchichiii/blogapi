import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .messages import STANDARD_MESSAGES


class MinimumLengthValidator:
    """Validator to check if the password meets the minimum length requirement."""

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                STANDARD_MESSAGES.get('PASSWORD_TOO_SHORT', {
                    'message': _("This password must contain at least %(min_length)d characters."),
                    'type': 'error'
                })['message'],
                code='password_too_short',
                params={'min_length': self.min_length},
            )


class SymbolValidator:
    """Validator to ensure the password contains at least one special symbol."""

    def validate(self, password, user=None):
        if not re.findall(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                STANDARD_MESSAGES.get('PASSWORD_NO_SYMBOL', {
                    'message': _("The password must contain at least one symbol: !@#$%^&*(),.?\":{}|<>"),
                    'type': 'error'
                })['message'],
                code='password_no_symbol',
            )


class UppercaseValidator:
    """Validator to require at least one uppercase letter in the password."""

    def validate(self, password, user=None):
        if not re.findall(r'[A-Z]', password):
            raise ValidationError(
                STANDARD_MESSAGES.get('PASSWORD_NO_UPPER', {
                    'message': _("The password must contain at least one uppercase letter, A-Z."),
                    'type': 'error'
                })['message'],
                code='password_no_upper',
            )


class NumberValidator:
    """Validator to ensure the password includes at least one numeric digit."""

    def validate(self, password, user=None):
        if not re.findall(r'\d', password):
            raise ValidationError(
                STANDARD_MESSAGES.get('PASSWORD_NO_NUMBER', {
                    'message': _("The password must contain at least one number, 0-9."),
                    'type': 'error'
                })['message'],
                code='password_no_number',
            )
