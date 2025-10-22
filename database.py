from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool


# URL БД
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./database.db"


# Асинзронный движок для работы с БД
engine = create_async_engine(SQLALCHEMY_DATABASE_URL,
                             connect_args={"check_same_thread": False},
                             poolclass=StaticPool,
                             echo=True)


# Фабрика сессий для асинхронной работы
AsyncSessionLocal = sessionmaker(engine,
                                 class_=AsyncSession,
                                 expire_on_commit=False,
                                 autocommit=False,
                                 autoflush=False)


# Базовый класс для всех моделей SQLAlchemy
Base = declarative_base()


# Генератор сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
