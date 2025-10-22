from sqlalchemy import Column, Integer, String, Numeric
from database import Base


# Модель товара для БД
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index = True, nullable=False)
    description = Column(String(500))
    price = Column(Numeric(10,2), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
