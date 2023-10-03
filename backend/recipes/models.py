from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User
from users.validators import validate_name


class Tag(models.Model):
    name = models.CharField('Тег', max_length=settings.MAX_LENGTH_VALUE,
                            unique=True, validators=[validate_name])
    color = models.CharField('Цвет тега', max_length=settings.MAX_LENGTH_COLOR,
                             unique=True, default='#ffffff')
    slug = models.SlugField('Слаг тега', max_length=settings.MAX_LENGTH_VALUE,
                            unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:settings.NAME_MAX_LENGTH]


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=settings.MAX_LENGTH_VALUE,
        validators=[validate_name]
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=settings.MAX_LENGTH_VALUE
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_for_ngredient',
            ),
        )

    def __str__(self):
        return self.name[:settings.NAME_MAX_LENGTH]


class Recipe(models.Model):
    name = models.CharField('Название рецепта',
                            max_length=settings.MAX_LENGTH_RECIPES_NAME)
    text = models.TextField('Описание рецепта')
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientAmount'
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
    tags = models.ManyToManyField(Tag, verbose_name='Теги',
                                  related_name='recipes')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return (
            f'Автор: {str(self.author)}'
            f'Название: {self.name[:settings.NAME_MAX_LENGTH]}'
        )


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='+',
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
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_recipe',
            ),
        )

    def __str__(self) -> str:
        return f'{self.ingredients} {self.amount}'


class BaseUserRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='+'
    )

    class Meta:
        abstract = True


class Favorite(BaseUserRecipe):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт в избранном',
        help_text='Рецепт в избранном',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_favorite_user_recipe'
            ),
        )

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(BaseUserRecipe):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_user_recipe',
            ),
        )

    def __str__(self):
        return f'{self.user} -> {self.recipe}'
