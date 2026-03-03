"""
routers/transactions.py — Endpoints de compras y historial.

POST /transactions/comprar        → Comprar 1 producto de una máquina (cliente)
GET  /transactions/me             → Mi historial
GET  /transactions/{id}           → Detalle de transacción
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.middleware.auth_middleware import get_current_user, require_role
from app.services import purchase_service as svc
from app.schemas.transaction import TransaccionResponse, TransaccionListResponse

router = APIRouter()


class ComprarRequest(BaseModel):
    """Compra de 1 slot de inventario (1 transacción = 1 producto en el schema de Supabase)."""
    inventario_id: UUID
    cantidad:      int          = Field(default=1, ge=1, le=10)
    promocion_id:  Optional[UUID] = None


@router.post(
    "/comprar",
    response_model=TransaccionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Comprar producto en máquina expendedora",
)
async def comprar(
    data: ComprarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Descuenta del wallet del cliente y reduce el inventario del slot.
    El trigger de Supabase registra automáticamente el movimiento en historial_inventario.
    """
    if current_user.rol.nombre != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden realizar compras",
        )
    try:
        tx = await svc.procesar_compra_item(
            current_user.id, data.inventario_id, data.cantidad, db, data.promocion_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(e))
    return TransaccionResponse.model_validate(tx)


@router.get(
    "/me",
    response_model=TransaccionListResponse,
    summary="Mi historial de compras",
)
async def my_historial(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    items, total = await svc.get_historial_cliente(current_user.id, db, limit)
    return TransaccionListResponse(
        total=total,
        transacciones=[TransaccionResponse.model_validate(t) for t in items],
    )


@router.get(
    "/{tx_id}",
    response_model=TransaccionResponse,
    summary="Detalle de transacción",
)
async def get_transaccion(
    tx_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    tx = await svc.get_transaccion(tx_id, db)
    if not tx:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    if current_user.rol.nombre == "cliente" and tx.cliente_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso a esta transacción")
    return TransaccionResponse.model_validate(tx)
