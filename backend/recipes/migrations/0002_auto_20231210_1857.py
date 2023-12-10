# Generated by Django 3.2 on 2023-12-10 15:57

from django.db import migrations, models
import recipes.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=200, validators=[recipes.validators.validate_name], verbose_name='Название ингредиента'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='name',
            field=models.CharField(max_length=30, validators=[recipes.validators.validate_name], verbose_name='Название рецепта'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(default='#ffffff', max_length=7, unique=True, validators=[recipes.validators.validate_hex], verbose_name='Цвет тега'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=200, unique=True, validators=[recipes.validators.validate_name], verbose_name='Тег'),
        ),
    ]
