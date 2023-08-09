from django.conf import settings
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        'Тег',
        max_length=200,
        unique=True,
        validators=[RegexValidator(r'^[a-zA-Z0-9_]*$',
                                   ('Допускаются только буквы, '
                                    'цифры и символы подчеркивания.'))]
    )
    color = models.CharField('Цвет в HEX', max_length=7,
                             unique=True, default='#18c4e8')
    slug = models.SlugField('Слаг тега', max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('id',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'color'), name='unique_for_tag'
            ),
        )

    def __str__(self):
        return self.name[:settings.NAME_MAX_LENGTH]


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_for_ngredient',
            ),
        )

    def __str__(self):
        return self.name[:settings.NAME_MAX_LENGTH]


class Recipe(models.Model):
    name = models.CharField('Название рецепта', max_length=30)
    text = models.TextField('Описание рецепта')
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовлени в минутах',
        default=settings.MIN_VALUE,
        validators=(
            MinValueValidator(
                settings.MIN_VALUE,
                message=f'Минимальное значение {settings.MIN_VALUE}.',
            ),
            MaxValueValidator(
                settings.MAX_VALUE_COOKING_TIME,
                message=(f'Максимальное значение'
                         f'{settings.MAX_VALUE_COOKING_TIME}.'),
            ),
        ),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientAmount',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes', blank=False
    )
    date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-date',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_for_author',
            ),
        )

    def __str__(self):
        return (
            f'Автор: {str(self.author)}'
            f'Название: {self.name[:settings.NAME_MAX_LENGTH]}'
        )


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        default=settings.MIN_VALUE,
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                settings.MIN_VALUE,
                message=f'Минимальное значение {settings.MIN_VALUE}.',
            ),
            MaxValueValidator(
                settings.MAX_VALUE_AMOUNT,
                message=f'Максимальное значение {settings.MAX_VALUE_AMOUNT}.',
            ),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_recipe',
            ),
        )

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='Ingredient',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='Recipe',
    )
    amount = models.IntegerField(
        verbose_name='Amount',
    )

    class Meta:
        verbose_name = 'Ingredient amount'
        verbose_name_plural = 'Ingredients amount'

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_favorite'),
        )

    def __str__(self):
        return f'Добавленно в избранное {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='shopping'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='shopping'
    )

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Список Покупок'
        constraints = (
            models.UniqueConstraint(fields=('user', 'recipe'),
                                    name='unique_shopping_cart'),
        )

    def __str__(self):
        return f'Добавил в корзину {self.recipe}'
