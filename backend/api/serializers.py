import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredients, ShoppingCart, Tag)
from users.models import Follow, User


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user
            and user.is_authenticated
            and Follow.objects.filter(user=user, author=obj).exists()
        )


class FollowSerializer(CustomUserSerializer):
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )
    recipes = SerializerMethodField(method_name='get_recipes')
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'recipes_count', 'recipes', 'is_subscribed')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data

    def validate(self, data):
        author_id = (
            self.context.get('request').parser_context.get('kwargs').get('id')
        )
        author = get_object_or_404(User, id=author_id)
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


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeShortSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('name', 'image', 'cooking_time')


class IngredientRecipeCreateSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount', 'name', 'measurement_unit')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.ingredient.id
        return data


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeCreateSerializer(
        source='recipeingredients', many=True
    )
    image = Base64ImageField(required=False, allow_null=True)
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


class RecipeCreateSerializer(ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeCreateSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time',)

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
        ingredients_list = []
        for item in ingredients:
            if item['id'] in ingredients_list:
                raise ValidationError(
                    {'ingredients': 'Ингредиенты не могут повторяться'}
                )
            ingredients_list.append(item['id'])
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
                        'Время приготовления рецепта не может меньше 1 мин.'
                    )
                }
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance, context=context).data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        name = validated_data.get('name')
        if Recipe.objects.filter(name=name).exists():
            raise ValidationError({'name': 'Название рецепта уже существует'})
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients', None)

        name = validated_data.get('name')
        if Recipe.objects.filter(name=name).exists():
            raise ValidationError({'name': 'Название рецепта уже существует'})

        if ingredients is not None:
            instance.ingredients.clear()
            for ingredient in ingredients:
                amount = ingredient['amount']
                RecipeIngredients.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient.get('id'),
                    defaults={'amount': amount},
                )
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):

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
