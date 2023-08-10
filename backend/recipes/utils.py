import re

from django.core.exceptions import ValidationError


def hex_color_validator(color):
    color = color.strip(' #')
    if not re.match(r'^([0-9a-fA-F]{3}){1,2}$', color):
        raise ValidationError(f'{color} не шестнадцатиричное.')
    if len(color) == 3:
        return f'#{color[0] * 2}{color[1] * 2}{color[2] * 2}'.upper()
    return f'#{color.upper()}'
