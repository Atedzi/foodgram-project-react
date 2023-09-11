## Описание проекта Foodgram
Сервис для гурманов и начинающих кулинаров. На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов в виде файла формата .txt, необходимых для приготовления одного или нескольких выбранных блюд.

***
## Для демонстрации возможностей, проект развернут на хостинге.
Ссылка на сайт: http://foodgram-atedzi.hopto.org/

Никнейм аккаунта суперпользователя:
```
foodgram_user 
```
Пароль:
```
foodgram_password
```

***
## Используемые технологии
- Django 3.2.16
- Django Rest Framework 3.14.0
- Gunicorn 20.1.0
- Nginx
- PostgreSQL
- Docker
- Docker-compose

***
## Как развернуть проект

Перейти в каталог, где будет размещен проект:
```
cd <путь_к_каталогу>
```
Клонировать проект из репозитория:
```
git clone https://github.com/Atedzi/foodgram-project-react.git
```
Перейти в каталог с проектом:
```
cd foodgram-project-react
```
Установить виртуальное окружение:
```
python3 -m venv venv
```
Активировать виртуальное окружение:
```
source venv/source/activate
```
Установить зависимости:
```
pip install -r requirements.txt
```
Выполнить в директории infra команду для сборки контейнеров:
```
docker-compose up -d --build
```
Выполнить миграции:
```
docker-compose exec backend python manage.py migrate
```
Создать суперюзера:
```
docker-compose exec backend python manage.py createsuperuser
```
Собрать статику:
``` 
docker-compose exec backend python manage.py collectstatic --no-input
``` 
Наполните базу данных ингредиентами и тегами. Выполните команду из директории ./backend/ :
```
docker-compose exec backend python manage.py import_database_tags 
docker-compose exec backend python manage.py import_database

```
Остановить проект:
```
docker-compose down
```
Теперь сервис доступен на вашем компьютере по вашему адресу хоста:
```
http://127.0.0.1/
```
Админка сервиса доступна по адресу:
```
http://127.0.0.1/admin/
```

***
## Подготовка к запуску проекта на удаленном сервере (пока не доступно)

- Войдите в свой удаленный сервер
- Склонируйте репозиторий на локальную машину
- Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:
- Отредактируйте файл конфигурации nginx
- Cоздайте и заполните файл .env в директории infra
```
DB_ENGINE=django.db.backends.postgresql
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DB_HOST=db
DB_PORT=5432
TOKEN=ваш-токен
ALLOWED_HOSTS=ваш-хост
```

Для работы с Workflow добавьте в Secrets GitHub переменные окружения для работы:
```
DB_ENGINE=<django.db.backends.postgresql>
DB_NAME=<имя базы данных postgres>
DB_USER=<пользователь бд>
DB_PASSWORD=<пароль>
DB_HOST=<db>
DB_PORT=<5432>
    
DOCKER_PASSWORD=<пароль от DockerHub>
DOCKER_USERNAME=<имя пользователя>
    
SECRET_KEY=<секретный ключ проекта django>

USER=<username для подключения к серверу>
HOST=<IP сервера>
PASSPHRASE=<пароль для сервера, если он установлен>
SSH_KEY=<ваш SSH ключ (для получения команда: cat ~/.ssh/id_rsa)>

TELEGRAM_TO=<ID чата, в который придет сообщение>
TELEGRAM_TOKEN=<токен вашего бота>
```
Workflow состоит из следующих шагов:
- Проверка кода на соответствие PEP8
- Сборка и публикация образа бекенда на DockerHub.
- Автоматический деплой на удаленный сервер.
- Отправка уведомления в телеграм-чат.

Затем выполните шаги, указанные в "Как развернуть проект", начиная с команды для сборки коннтенеров.

***
## Возможности API
С возможностями API вы можете ознакомиться в форматe ReDoc, перейдя по ссылке: 
- пока не доступно

***
## Автор

frontend: Яндекс Практикум;
backend, DevOps: Квашин Сергей - https://github.com/Atedzi;
Ревьюер: Андрей Тюрин.
