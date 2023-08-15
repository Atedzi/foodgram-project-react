import re

from django.core.exceptions import ValidationError


def validate_name(value):
    if not re.match(r'^[а-яА-Яa-zA-Z0-9_ ]*$', value):
        raise ValidationError(
            ('Допускаются только буквы, цифры, символ подчеркивания и пробел.')
        )
