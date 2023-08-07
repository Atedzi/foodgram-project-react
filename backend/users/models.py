from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')
    username = models.CharField('Логин', max_length=150, unique=True,)
    email = models.EmailField('Email', max_length=254, unique=True,)
    first_name = models.CharField('Имя', max_length=150,)
    last_name = models.CharField('Фамилия', max_length=150,)
    password = models.CharField('Пароль', max_length=150)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)
        constraints = (
            models.UniqueConstraint(
                fields=('email', 'username'), name='unique_auth'
            ),
        )

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
        )

    def __str__(self):
        return f'Пользователь {self.user} подписан на {self.author}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписываться на самого себя')
        super(Follow, self).clean()
