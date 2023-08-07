import json

from django.core.management import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.fill_tags()

    def fill_tags(self):
        with open('./data/tags.json', 'r', encoding='utf-8') as t:
            data = json.load(t)

        for row in data:
            tag, _ = Tag.objects.update_or_create(
                name=row['name'],
                defaults={'color': row['color'], 'slug': row['slug']}
            )
            tag.save()
