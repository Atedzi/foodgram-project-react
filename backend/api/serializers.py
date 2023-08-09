from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Tag)
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from users.models import Follow, User


class CustomUserSerializer(ModelSerializer):
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
    recipes_limit = None

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'recipes_count', 'recipes', 'is_subscribed')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes(self, obj):
        if self.recipes_limit is not None:
            recipes = obj.recipes.all()[:self.recipes_limit]
        else:
            recipes = obj.recipes.all()
        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data

    def to_representation(self, instance):
        self.recipes_limit = (
            self.context.get('request').query_params.get('recipes_limit')
        )
        return super().to_representation(instance)

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


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


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
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time',)

    def get_ingredients(self, recipe):
        ingredients_data = recipe.ingredients.through.objects.filter(
            recipe=recipe).values('ingredients__id', 'ingredients__name',
                                  'ingredients__measurement_unit', 'amount')
        return ingredients_data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredients_data = representation['ingredients']
        ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredient = {
                'id': ingredient_data['ingredients__id'],
                'name': ingredient_data['ingredients__name'],
                'measurement_unit': ingredient_data[
                    'ingredients__measurement_unit'],
                'amount': ingredient_data['amount']
            }
            ingredients_list.append(ingredient)
        representation['ingredients'] = ingredients_list
        return representation

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
    ingredients = IngredientRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients',
                  'name', 'image', 'text', 'cooking_time',)

    def get_ingredients(self, recipe):
        return recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('ingredient__amount'))

    def create_ingredients(self, ingredients, recipe):
        list_ingredients = []
        for ingredient in ingredients:
            list_ingredients.append(
                RecipeIngredients(
                    recipe=recipe,
                    ingredients=ingredient['id'],
                    amount=ingredient['amount'],
                )
            )
        RecipeIngredients.objects.bulk_create(list_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        ingreds = validated_data.pop('ingredients', None)
        if ingreds is not None:
            RecipeIngredients.objects.filter(recipe=instance).delete()
            self.create_ingredients(ingreds, instance)
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
