from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from recipes.models import (Favorite, Ingredient, Recipe, IngredientAmount,
                            ShoppingCart, Tag)
from users.models import User


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.follower.filter(author=obj).exists()


class FollowSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )
    is_subscribed = serializers.BooleanField(default=True)
    recipes = serializers.SerializerMethodField(method_name='get_recipes')

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'recipes_count', 'recipes', 'is_subscribed')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]
        serializer = RecipeShortSerializer(recipes, many=True)
        return serializer.data

    def validate(self, data):
        author_id = (
            self.context.get('request').parser_context.get('kwargs').get('pk')
        )
        author = get_object_or_404(User, pk=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeShortSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientAmountSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                source='ingredient.id',)
    name = serializers.CharField(source='ingredient.name',
                                 read_only=True,)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True,)
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(many=True,
                                             source='recipe_ingredients')
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user
            and user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user
            and user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipeCreateSerializer(ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'author',
                  'name', 'image', 'text', 'cooking_time',)
        read_only_fields = ('id',)

    @staticmethod
    def create_ingredients(recipe, ingredients):
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(
                IngredientAmount(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
            )
        IngredientAmount.objects.bulk_create(recipe_ingredients)

    @transaction.atomic()
    def create(self, validated_data):
        request = self.context.get('request', None)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.recipe_ingredients.all().delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def validate_tags(self, data):
        tags = self.initial_data.get('tags', False)
        if not tags:
            raise ValidationError({'tags': 'Нельзя добавить рецепт без тега'})
        tags_list = []
        for tags in tags:
            if tags in tags_list:
                raise ValidationError(
                    {'tags': 'Повторяющиеся теги'}
                )
            tags_list.append(tags)
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Нельзя добавить рецепт без ингредиентов'}
            )
        unique_ingredients = []
        for item in ingredients:
            if item['id'] in unique_ingredients:
                raise ValidationError(
                    {'ingredients': 'Ингредиенты не могут повторяться'}
                )
            unique_ingredients.append(item['id'])
            if int(item['amount']) < 1:
                raise ValidationError(
                    {
                        'amount': (
                            'Количество ингредиентов не может быть меньше 1'
                        )
                    }
                )
        return data

    def validate_cooking_time(self, data):
        cooking_time = self.initial_data.get('cooking_time')
        if int(cooking_time) <= 0:
            raise ValidationError(
                {
                    'cooking_time': (
                        'Время приготовления не может быть меньше 1 мин.'
                    )
                }
            )
        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(ModelSerializer):

    class Meta(RecipeShortSerializer.Meta):
        fields = RecipeShortSerializer.Meta.fields

    def validate(self, data):
        recipe_pk = (
            self.context.get('request').parser_context.get('kwargs').get('pk')
        )
        recipe = get_object_or_404(Recipe, pk=recipe_pk)
        user = self.context.get('request').user
        if user.favorites.filter(recipe=recipe).exists():
            raise ValidationError('Уже в избранном.')
        return data


class FavoriteShoppingCartSerializer(RecipeShortSerializer):

    class Meta(RecipeShortSerializer.Meta):
        fields = RecipeShortSerializer.Meta.fields

    def validate(self, data):
        recipe_pk = (
            self.context.get('request').parser_context.get('kwargs').get('pk')
        )
        recipe = get_object_or_404(Recipe, pk=recipe_pk)
        user = self.context.get('request').user
        if user.shopping.filter(recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен')
        return data
