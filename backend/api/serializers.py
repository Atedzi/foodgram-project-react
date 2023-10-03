from django.db.models import F
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
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeShortSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('name', 'image', 'cooking_time')


class IngredientAmountSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount', 'name', 'measurement_unit')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['id'] = instance.ingredient.id
        return data


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer(read_only=True)
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time',)

    def get_ingredients(self, obj):
        ingredients = IngredientAmount.objects.filter(recipe=obj)
        return IngredientAmountSerializer(ingredients, many=True).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredients_data = representation['ingredients']
        ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredient = {
                'id': ingredient_data['ingredient__id'],
                'name': ingredient_data['ingredient__name'],
                'measurement_unit': ingredient_data[
                    'ingredient__measurement_unit'],
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
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'author',
                  'name', 'image', 'text', 'cooking_time',)

    def get_ingredients(self, recipe):
        return recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('ingredient__amount'))

    def create_ingredients(self, ingredients, recipe):
        list_ingredients = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient.get('id')
            )
            amount = ingredient.get('amount')
            list_ingredients.append(
                IngredientAmount(
                    recipe=recipe, ingredient=current_ingredient, amount=amount
                )
            )
        IngredientAmount.objects.bulk_create(ingredients)

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
            IngredientAmount.objects.filter(recipe=instance).delete()
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
        unique_ingredients = []
        for item in ingredients:
            if item['id'] in unique_ingredients:
                raise ValidationError(
                    {'ingredients': 'Ингредиенты не могут повторяться'}
                )
            unique_ingredients.append(item['id'])
            if item['amount'] < 1:
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
        if cooking_time <= 0:
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
