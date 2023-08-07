from string import hexdigits

from django.core.exceptions import ValidationError


def hex_color_validator(color):
    color = color.strip(' #')
    if len(color) not in (3, 6):
        raise ValidationError(
            f'Код цвета {color} не правильной длины ({len(color)}).'
        )
    if not set(color).issubset(hexdigits):
        raise ValidationError(f'{color} не шестнадцатиричное.')
    if len(color) == 3:
        return f'#{color[0] * 2}{color[1] * 2}{color[2] * 2}'.upper()
    return f'#{color.upper()}'
