# 📝 FastAPI Blog

Асинхронный backend для блога на FastAPI.
Приложение содержит **4** Docker-контейнера:
- PostgreSQL (postgres_db) - база данных
- Приложение (fastapi_app) - основное приложение
- Celery (celery) - асинхронная очередь задач (для удаления медиа)
- Redis (redis) - брокер сообщений (бэкенд для Celery)

Хранение медиа реализовано с помощью [Yandex Disk.](https://yandex.ru/dev/disk-api/doc/ru/concepts/quickstart "API Диска")   

## 📁 Клонирование репозитория
```bash
git clone https://github.com/AlekseyRodimkin/fastapi_blog.git
cd fastapi_blog
```

## ⚙️ Настройка переменных окружения
Создайте файл .env в корне проекта, скопировав шаблон и заполните своими данными.
```bash
cp .env.template .env
```

## 💿 Создание папки приложения на Яндекс Диске
Перейдите по [ссылке](https://oauth.yandex.ru/client/new/ "Создание приложения") для создания папки приложения, получите токен и разместите его в .env файле

## 🐳 Установка и запуск через Docker Compose
##### Сборка и запуск контейнеров

```bash
docker compose up -d
```

## 🔨 Проверка работоспособности
Корневой эндпоинт для проверки работы доступен по адресу: <http://localhost:8000/api/healthchecker>

📚 Документация API (Swagger UI)  
После запуска приложения будет доступна автоматическая документация по адресу:
<http://localhost:8000/docs>  
Логи приложения находятся в файлах:  **logs/app_debug.log, logs/app_error.log**  
Логи тестов находятся в файлах:  **logs/test_debug.log, logs/test_error.log**  

Что можно найти в Swagger:
- Полный список доступных маршрутов
- Поддерживаемые HTTP-методы
- Форматы запросов
<img src="https://github.com/AlekseyRodimkin/fastapi_blog/blob/main/README/routes.png" width="700">
- Модели данных (Pydantic схемы)
<img src="https://github.com/AlekseyRodimkin/fastapi_blog/blob/main/README/schemas.png" width="700">

## 🗂 Структура проекта
```text
.
├── alembic                                 
│   ├── env.py
│   ├── __pycache__
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 2d4090af011d_create_tables.py  # миграция
│       └── __pycache__
├── app
│   ├── app.py                        # приложение + /api/healthchecker
│   ├── events.py                     # шаблон тригера
│   ├── __init__.py
│   ├── models.py                     # модели
│   ├── routes                        # роуты
│   │   ├── __init__.py
│   │   ├── medias.py                      
│   │   ├── tweets.py
│   │   └── users.py
│   ├── schemas                       # схемы Pydantic
│   │   ├── __init__.py
│   │   ├── tweet_schema.py
│   │   └── user_schema.py
│   └── services
│       ├── decorators.py             # декораторы
│       ├── __init__.py
│       ├── media_service.py          # функции для работы с медиа
│       ├── tweet_service.py          # функции для работы с постами
│       ├── user_service.py           # функции для работы с пользователями
│       ├── yandex.py                 # функции для работы с диском
│       └── utils.py                  # остальные функции
├── config
│   ├── config.py                     # основной конфиг
│   ├── __init__.py
│   ├── logging_config.py             # конфиг логирования
├── tests
│   ├── conftest.py                   # фикстуры
│   ├── __init__.py
│   ├── fastapi_blog.postman_collection.json    # коллекция для тестирования в Postman
│   ├── test_files                              # тестовые изображения
│   │   ├── test_image_1.jpeg
│   │   ├── test_image_2.jpeg
│   │   └── test_image_3.jpeg
│   ├── test_media.py
│   ├── test_root.py
│   ├── test_tweet.py
│   └── test_user.py
└── uploads                      # папка для временных файлов
├── .env.template                # шаблон .env
├── .dockerignore          
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yaml
├── pyproject.toml
├── poetry.lock
├── scripts.py                  # скрипты Poetry
├── requirements.txt
├── .flake8
├── main.py                     # точка входа в приложение
├── README.md
```
