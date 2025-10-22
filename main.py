from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from decimal import Decimal
from typing import List, Optional
import asyncio

import models
import schemas
from database import get_db, engine

# Создание экземпляра FastAPI приложения
app = FastAPI(
    title="Items API",
    description="Simple CRUD API for items management with Decimal prices",

)


# Создание таблицы в БД при запуске, если они не существуют
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


# Добавление товара
@app.post("/items/",
          response_model=schemas.Item,
          status_code=status.HTTP_201_CREATED,
          tags=["Creating"],
          summary="Create item",
          description="Create a new item in the database with transaction support",
          responses={
              201: {"description": "Item created successfully"},
              400: {"description": "Validation error"},
              500: {"description": "Database error"}
          })
async def create_item(item: schemas.ItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Создаем объект SQLAlchemy из Pydantic схемы
        db_item = models.Item(**item.dict())

        db.add(db_item)
        await db.commit()

        result = await db.execute(select(models.Item).where(models.Item.id == db_item.id))
        created_item = result.scalar_one()
        return created_item

    except IntegrityError as e:
        # Откатываем транзакцию при ошибке целостности данных
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}"
        )
    except Exception as e:
        # Откатываем при любых других ошибках
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Получение всех товаров
@app.get("/items/",
         response_model=List[schemas.Item],
         tags=["Viewing"],
         summary="List items",
         description="Get list of all items with optional filtering and pagination",
         responses={
             200: {"description": "Successful operation"},
             500: {"description": "Database error"}
         })
async def list_items(
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
        min_price: Optional[Decimal] = Query(None, ge=0, description="Filter by minimum price"),
        max_price: Optional[Decimal] = Query(None, ge=0, description="Filter by maximum price"),
        name_contains: Optional[str] = Query(None, description="Filter by name containing string"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получение списка товаров с пагинацией и фильтрацией.

    Параметры:
    - skip: количество элементов для пропуска (пагинация)
    - limit: ограничение количества элементов в ответе (1-1000)
    - min_price: минимальная цена для фильтрации
    - max_price: максимальная цена для фильтрации
    - name_contains: фильтр по частичному совпадению в названии
    """
    try:
        # Базовый запрос
        query = select(models.Item)

        # Применение фильтров, если параметры переданы
        if min_price is not None:
            # WHERE price >= min_price
            query = query.where(models.Item.price >= min_price)
        if max_price is not None:
            # WHERE price <= max_price
            query = query.where(models.Item.price <= max_price)
        if name_contains:
            # WHERE name LIKE '%name_contains%'
            query = query.where(models.Item.name.contains(name_contains))

        # Добавление пагинации и выполнение запроса
        result = await db.execute(query.offset(skip).limit(limit))

        # Извлечение экземпляров
        items = result.scalars().all()
        return items

    except Exception as e:
        # Обработка ошибок
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# Получение конкретного товара
@app.get("/items/{item_id}",
         response_model=schemas.Item,
         tags=["Viewing"],
         summary="Get item",
         description="Get a specific item by its ID",
         responses={
             200: {"description": "Successful operation"},
             404: {"description": "Item not found"},
             500: {"description": "Database error"}
         })
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Выполнение запроса на получение
        result = await db.execute(
            select(models.Item).where(models.Item.id == item_id)
        )

        # Получаем один результат или None
        db_item = result.scalar_one_or_none()

        # Проверка на существование товара
        if db_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return db_item

    except HTTPException:
        raise
    except Exception as e:
        # Обработка всех остальных ошибок
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# Обновление товара
@app.put("/items/{item_id}",
         response_model=schemas.Item,
         tags=["Changing"],
         summary="Update item",
         description="Update an existing item by its ID with transaction support",
         responses={
             200: {"description": "Item updated successfully"},
             404: {"description": "Item not found"},
             400: {"description": "Validation error"},
             500: {"description": "Database error"}
         })
async def update_item(item_id: int, item: schemas.ItemUpdate, db: AsyncSession = Depends(get_db)):
    # Настройки механизма повторных попыток
    max_retries = 3
    retry_delay = 0.1

    # Цикл повторных попыток для обработки блокировок БД
    for attempt in range(max_retries):
        try:
            # Проверка существования товара
            result = await db.execute(select(models.Item).where(models.Item.id == item_id))
            existing_item = result.scalar_one_or_none()
            if existing_item is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

            # Подготавливаем данные для обновления, убираем None значения
            # Используем model_dump(exclude_unset=True) для получения только переданных полей
            update_data = item.model_dump(exclude_unset=True)

            # Если не передано ни одного поля для обновления
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update provided"
                )

            # Обрабатываем Decimal поля для базы данных
            if 'price' in update_data and isinstance(update_data['price'], str):
                update_data['price'] = Decimal(update_data['price'])

            update_stmt = (
                update(models.Item)
                .where(models.Item.id == item_id)
                .values(**update_data)
            )

            result = await db.execute(update_stmt)

            await db.commit()

            # Получаем обновленный товар для возврата
            result = await db.execute(
                select(models.Item).where(models.Item.id == item_id)
            )
            updated_item = result.scalar_one()

            return updated_item

        except OperationalError as e:
            # Обработка ошибок блокировки БД
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                # Откатываем транзакцию и ждем перед повторной попыткой
                await db.rollback()
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            else:
                # Превышено максимальное количество попыток
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database is busy, please try again later"
                )
        except IntegrityError as e:
            # Ошибка целостности данных (уникальность, проверки)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(e)}"
            )
        except Exception as e:
            # Любые другие ошибки
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )

    # Если все попытки исчерпаны
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Max retries exceeded for update operation"
    )


# Удаление товара
@app.delete("/items/{item_id}",
            summary="Delete item",
            tags=["Deleting"],
            description="Delete a specific item by its ID with transaction support",
            responses={
                200: {"description": "Item deleted successfully"},
                404: {"description": "Item not found"},
                500: {"description": "Database error"}
            })
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Проверка существования товара
        result = await db.execute(
            select(models.Item).where(models.Item.id == item_id)
        )
        db_item = result.scalar_one_or_none()

        if db_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        await db.delete(db_item)

        await db.flush()

        return {"message": "Item deleted successfully"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        # Обрабатываем все остальные ошибки
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)