from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models

from recipes.utils import hex_color_validator

from users.models import User

STR_MAX_LENGTH = 25
MIN_VALUE_AMOUNT = 1
MAX_VALUE_AMOUNT = 1000
MIN_VALUE_COOKING_TIME = 1
MAX_VALUE_COOKING_TIME = 500


class Tag(models.Model):
    name = models.CharField('Тег', max_length=200, unique=True)
    color = models.CharField(
        'Цвет в HEX',
        max_length=7,
        unique=True,
        validators=(
            RegexValidator(
                regex=r'^#([A-Fa-f0-9]{6})$',
                message='Поле должно содержать HEX-код выбранного цвета.',
            ),
        ),
    )
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
        return self.name[:STR_MAX_LENGTH]

    def clean(self):
        self.name = self.name.strip().lower()
        self.slug = self.slug.strip().lower()
        self.color = hex_color_validator(self.color)
        return super().clean()


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
        return self.name[:STR_MAX_LENGTH]


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
        default=MIN_VALUE_COOKING_TIME,
        validators=(
            MinValueValidator(
                MIN_VALUE_COOKING_TIME,
                message=f'Минимальное значение {MIN_VALUE_COOKING_TIME}.',
            ),
            MaxValueValidator(
                MAX_VALUE_COOKING_TIME,
                message=f'Максимальное значение {MAX_VALUE_COOKING_TIME}.',
            ),
        ),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredients',
        related_name='recipes',
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
            f'Автор: {str(self.author)} Название: {self.name[:STR_MAX_LENGTH]}'
        )


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipeingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='recipeingredients',
    )
    amount = models.PositiveSmallIntegerField(
        default=MIN_VALUE_AMOUNT,
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                MIN_VALUE_AMOUNT,
                message=f'Минимальное значение {MIN_VALUE_AMOUNT}.',
            ),
            MaxValueValidator(
                MAX_VALUE_AMOUNT,
                message=f'Максимальное значение {MAX_VALUE_AMOUNT}.',
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


class FavoritesAndShopping(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(FavoritesAndShopping):

    class Meta(FavoritesAndShopping.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorites'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_favorite'
            ),
        )


class ShoppingCart(FavoritesAndShopping):

    class Meta(FavoritesAndShopping.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        default_related_name = 'shopping'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_shopping_cart'
            ),
        )
