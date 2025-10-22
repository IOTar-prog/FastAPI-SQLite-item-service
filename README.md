FastAPI Items API

Простое REST API для управления товарами, реализованное на FastAPI с SQLite.

🚀 Возможности

· ✅ Полный CRUD (Create, Read, Update, Delete)  
· ✅ Асинхронные операции  
· ✅ Валидация данных с Pydantic  
· ✅ Decimal для точных цен  
· ✅ Фильтрация, сортировка и пагинация  
· ✅ Автоматическая документация Swagger  
· ✅ Готовый Docker-контейнер  

📋 Эндпоинты

Метод URL | Описание  
POST /items/ | Создать товар  
GET /items/ | Список товаров (с фильтрацией)  
GET /items/{id} | Получить товар по ID  
PUT /items/{id} | Обновить товар  
DELETE /items/{id} | Удалить товар  

🛠 Установка и запуск

Локальная установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/IOTar-prog/FastAPI-SQLite-item-service.git
```

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

1. Запустите приложение:

```bash
uvicorn main:app --reload
```

1. Откройте в браузере:

```
http://localhost:8000/docs
```

Запуск в Docker

1. Соберите и запустите контейнер:

```bash
docker-compose up --build
```

1. Приложение будет доступно по адресу:

```
http://localhost:8000/docs
```

📖 Примеры использования

Создание товара

```bash
curl -X POST "http://localhost:8000/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ноутбук",
    "description": "Игровой ноутбук",
    "price": "999.99",
    "quantity": 10
  }'
```

Получение списка товаров с фильтрацией

```bash
curl "http://localhost:8000/items/?min_price=100&max_price=1000&in_stock_only=true"
```

Обновление товара

```bash
curl -X PUT "http://localhost:8000/items/1" \
  -H "Content-Type: application/json" \
  -d '{"price": "899.99", "quantity": 5}'
```

🎯 Фильтры для GET /items/

· min_price / max_price - фильтр по цене  
· min_quantity / max_quantity - фильтр по количеству  
· name_contains - поиск по названию  
· in_stock_only - только товары в наличии  
· sort_by - поле для сортировки (name, price, quantity, id)  
· sort_order - направление сортировки (asc, desc)  
· skip / limit - пагинация  

🗄 Структура проекта

```
fastapi-items-api/
├── main.py          # Основное приложение FastAPI
├── models.py        # Модели SQLAlchemy
├── schemas.py       # Pydantic схемы
├── database.py      # Настройка базы данных
├── requirements.txt # Зависимости
├── Dockerfile       # Конфигурация Docker
└── docker-compose.yml # Docker Compose
```

🔧 Технологии

· FastAPI  
· SQLAlchemy  
· Pydantic  
· SQLite  
· Docker  
