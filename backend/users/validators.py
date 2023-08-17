import re

from django.core.exceptions import ValidationError


def validate_name(value):
    if not re.match(r'^[а-яА-Яa-zA-Z0-9_@+.-]*$', value):
        raise ValidationError(
            ('Допускаются только буквы, цифры и символы _, -, @, +.')
        )


def validate_first_last_name(value):
    if not re.match(r'^[а-яА-Яa-zA-Z ]*$', value):
        raise ValidationError(
            ('Допускаются только буквы и пробел.')
        )
