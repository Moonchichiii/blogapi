import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class MinimumLengthValidator:
    """Check if password meets minimum length requirement."""
    def __init__(self, min_length=8):
        self.min_length = min_length
    def __call__(self, password):
        if len(password) < self.min_length:
            raise ValidationError(
                _("This password must contain at least %(min_length)d characters."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

class SymbolValidator:
    """Require at least one symbol in the password."""
    def validate(self, password, user=None):
        if not any(char in '!@#$%^&*(),.?":{}|<>' for char in password):
            raise ValidationError(
                _("The password must contain at least one symbol: !@#$%^&*(),.?\":{}|<>"),
                code='password_no_symbol',
            )
    def get_help_text(self):
        return _("Your password must contain at least one symbol: !@#$%^&*(),.?\":{}|<>")

class UppercaseValidator:
    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError(
                _("The password must contain at least one uppercase letter, A-Z."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter, A-Z.")

class NumberValidator:
    def validate(self, password, user=None):
        if not any(char.isdigit() for char in password):
            raise ValidationError(
                _("The password must contain at least one digit, 0-9."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Your password must contain at least one number, 0-9.")