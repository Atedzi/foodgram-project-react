from django import forms
from django.contrib import admin
from django.utils.html import format_html

from recipes.models import (Favorite, Ingredient, Recipe,
                            IngredientAmount, ShoppingCart, Tag)


class RecipeIngredientsInLine(admin.TabularInline):
    model = IngredientAmount


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    ordering = ('name',)
    empty_value_display = '-пусто-'
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    ordering = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        ingredients = cleaned_data.get('ingredients')
        if not ingredients or ingredients.count() == 0:
            raise forms.ValidationError(
                'Необходимо добавить хотя бы один ингредиент')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    list_display = ('id', 'name', 'author', 'text',
                    'cooking_time', 'image_tag',
                    'favorite_count', 'pub_date')
    list_display_links = ('name',)
    search_fields = ('name', 'author', 'text', 'cooking_time')
    list_filter = ('name', 'author', 'tags')
    readonly_fields = ('favorite_count',)
    inlines = (RecipeIngredientsInLine,)
    ordering = ('-pub_date',)
    empty_value_display = '-пусто-'

    def favorite_count(self, obj):
        return obj.favorites.count()

    def image_tag(self, obj):
        return format_html(
            '<img src="{}" width="120" heigh="65" />'.format(obj.image.url)
        )
    image_tag.short_description = 'Картинка'

    @admin.display(description='Список ингредиентов')
    def ingredients_list(self, recipe):
        return [ingredient.name for ingredient in recipe.ingredients.all()]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    ordering = ('id',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    ordering = ('id',)
    empty_value_display = '-пусто-'
