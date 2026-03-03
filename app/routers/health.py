"""Router principal de salud de la API."""
from fastapi import APIRouter
from app.config import settings
from app.database import check_db_connection

router = APIRouter()


@router.get("/health", summary="Verificar estado de la API y conexión a BD")
async def health_check():
    """
    Endpoint de salud. Verifica:
    - Que la API está corriendo
    - Que la conexión a Supabase/PostgreSQL está activa
    """
    db_ok = await check_db_connection()
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.app_env,
        "database": "connected" if db_ok else "disconnected",
    }
