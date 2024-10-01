import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinimumLengthValidator:
    """Validator to check if the password meets the minimum length requirement."""

    def __init__(self, min_length=8):
        """
        Initialize the validator with a minimum length.

        Args:
            min_length (int): The minimum length required for the password.
        """
        self.min_length = min_length

    def validate(self, password, user=None):
        """
        Validate the password length.

        Args:
            password (str): The password to validate.
            user (User, optional): The user object. Defaults to None.

        Raises:
            ValidationError: If the password is shorter than the minimum length.
        """
        if len(password) < self.min_length:
            raise ValidationError(
                _("This password must contain at least %(min_length)d characters."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )


class SymbolValidator:
    """Validator to ensure the password contains at least one special symbol."""

    def validate(self, password, user=None):
        """
        Validate the presence of a special symbol in the password.

        Args:
            password (str): The password to validate.
            user (User, optional): The user object. Defaults to None.

        Raises:
            ValidationError: If the password does not contain a special symbol.
        """
        if not re.findall(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("The password must contain at least one symbol: !@#$%^&*(),.?\":{}|<>"),
                code='password_no_symbol',
            )


class UppercaseValidator:
    """Validator to require at least one uppercase letter in the password."""

    def validate(self, password, user=None):
        """
        Validate the presence of an uppercase letter in the password.

        Args:
            password (str): The password to validate.
            user (User, optional): The user object. Defaults to None.

        Raises:
            ValidationError: If the password does not contain an uppercase letter.
        """
        if not re.findall(r'[A-Z]', password):
            raise ValidationError(
                _("The password must contain at least one uppercase letter, A-Z."),
                code='password_no_upper',
            )


class NumberValidator:
    """Validator to ensure the password includes at least one numeric digit."""

    def validate(self, password, user=None):
        """
        Validate the presence of a numeric digit in the password.

        Args:
            password (str): The password to validate.
            user (User, optional): The user object. Defaults to None.

        Raises:
            ValidationError: If the password does not contain a numeric digit.
        """
        if not re.findall(r'\d', password):
            raise ValidationError(
                _("The password must contain at least one number, 0-9."),
                code='password_no_number',
            )