"""
routers/promotions.py — Endpoints de promociones/descuentos.

GET  /promotions/     → Listar promociones activas (público)
"""
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/",
    summary="Listar promociones activas",
    response_model=list[dict],
)
async def list_promotions():
    """
    Placeholder — módulo de promociones en desarrollo.
    Retorna lista vacía hasta que se implemente la lógica de descuentos.
    """
    return []
