"""
database.py — Motor async SQLAlchemy conectado a Supabase via Session Pooler.

Usamos el Session Pooler de Supabase (puerto 5432 en el host del pooler), que:
- Mantiene conexiones persistentes a PostgreSQL → compatible con prepared statements
- Gestiona su propio pool → podemos usar pool_size en SQLAlchemy también
- No tiene las restricciones del Transaction Pooler (puerto 6543)
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings


engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy del proyecto."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency de FastAPI para inyectar sesión de BD en cada endpoint.
    Uso:
        @router.get("/ejemplo")
        async def endpoint(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Verifica conexión a la BD. Usado en /health."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"DB health check failed: {e}")
        return False
