from django.contrib import admin

from users.models import Follow, User


@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'last_name', 'first_name',
                    'email', 'is_staff', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('username', 'email', 'is_staff', 'date_joined')
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FolowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
