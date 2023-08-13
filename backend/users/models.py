from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validators import validate_name, validate_first_last_name


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    username = models.CharField(
        max_length=settings.MAX_LENGTH,
        unique=True,
        verbose_name='Username',
        validators=[validate_name]
    )
    email = models.EmailField(
        max_length=settings.MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name='Email'
    )
    first_name = models.CharField(
        max_length=settings.MAX_LENGTH,
        verbose_name='First name',
        validators=[validate_first_last_name]
    )
    last_name = models.CharField(
        max_length=settings.MAX_LENGTH,
        verbose_name='Last name',
        validators=[validate_first_last_name]
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower',)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following',)

    class Meta:
        ordering = ('-id',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='user_not_author'
            ),
        )

    def __str__(self):
        return f'Пользователь {self.user} подписан на {self.author}'
