import re

from django.core.exceptions import ValidationError


def validate_name(value):
    if not re.match(r'^[а-яА-Яa-zA-Z0-9_ ]*$', value):
        raise ValidationError(
            ('Допускаются только буквы, цифры, символ подчеркивания и пробел.')
        )


def validate_hex(value):
    if not re.match(r'^#([A-Fa-f0-9]6|[A-Fa-f0-9]3)', value):
        raise ValidationError(
            ('Неверный формат цвета. Допустимы '
             'только hex-коды вида #RRGGBB или #RGB.')
        )
