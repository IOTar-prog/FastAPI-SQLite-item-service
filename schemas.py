from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from typing import Optional, Any
import json


# JSON encoder для Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


# Базовая схема
class ItemBase(BaseModel):
    name: str = Field(...,
                      min_length=1,
                      max_length=50,
                      description="Item name")

    description: Optional[str] = Field(None,
                                       max_length=500,
                                       description="Item description")

    price: Decimal = Field(...,
                           ge=0,
                           description="Item price( >= 0 )")

    quantity: int = Field(...,
                          ge=0,
                          description="Item quantity ( >= 0 )")

    # Валидатор для цены. Проверяет отрицательность значения, оругляет до сотых, преобразовываает в Decimal.
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be positive')
        return v.quantize(Decimal('0.01'))

    # Переопределяем dict() для правильной сериализации Decimal.
    def dict(self, **kwargs) -> dict[str, Any]:
        d = super().model_dump(**kwargs)
        # Конвертируем Decimal в строку для JSON сериализации
        for key, value in d.items():
            if isinstance(value, Decimal):
                d[key] = str(value)
        return d

    model_config = ConfigDict(
        json_encoders={
            Decimal: str
        },
        from_attributes=True
    )


# Схема для создания товара
class ItemCreate(ItemBase):
    pass


# Схема для обновления товара
class ItemUpdate(ItemBase):
    name: Optional[str] = Field(...,
                                min_length=1,
                                max_length=50,
                                description="Item name")

    description: Optional[str] = Field(None,
                                       max_length=500,
                                       description="Item description")

    price: Optional[Decimal] = Field(...,
                                     ge=0,
                                     description="Item price( >= 0 )")

    quantity: Optional[int] = Field(...,
                                    ge=0,
                                    description="Item quantity ( >= 0 )")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be positive')
        return v.quantize(Decimal('0.01')) if v is not None else v

    # Переопределяем dict() для правильной сериализации Decimal.
    def dict(self, **kwargs) -> dict[str, Any]:
        d = super().model_dump(**kwargs)
        # Конвертируем Decimal в строку и убираем None значения
        result = {}
        for key, value in d.items():
            if value is not None:
                if isinstance(value, Decimal):
                    result[key] = str(value)
                else:
                    result[key] = value
        return result

    model_config = ConfigDict(
        json_encoders={
            Decimal: str
        },
        from_attributes=True
    )


# Схема для получения информации о товаре
class Item(ItemBase):
    id: int


class Config:
    # Создание экземпляров из ORM-объектов
    from_attributes = True
    # Конвертер Decimal в строку
    json_encoders = {Decimal: lambda v: str(v)}
