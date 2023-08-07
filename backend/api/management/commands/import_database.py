import json

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.fill_ingredients()
        self.fill_tags()

    def fill_ingredients(self):
        with open('./data/ingredients.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for row in data:
            ingredient, _ = Ingredient.objects.update_or_create(
                name=row['name'],
                defaults={'measurement_unit': row['measurement_unit']}
            )
            ingredient.save()
