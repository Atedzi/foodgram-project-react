import re

from django.core.exceptions import ValidationError


def hex_color_validator(color):
    color = color.strip('#')
    if not re.match(r'^([0-9a-fA-F]){3,6}$', color):
        raise ValidationError(f'{color} не является шестнадцатеричным цветом.')
    elif len(color) == 3:
        color = ''.join([c * 2 for c in color])
    return '#' + color.lower()
