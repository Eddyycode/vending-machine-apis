"""
routers/inventory.py — Endpoints de inventario por máquina.

GET    /inventory/{maquina_id}                       → Ver inventario
POST   /inventory/{maquina_id}/items                 → Agregar slot
PATCH  /inventory/{maquina_id}/items/{item_id}       → Actualizar slot
POST   /inventory/{maquina_id}/items/{item_id}/reponer → Reponer stock
DELETE /inventory/{maquina_id}/items/{item_id}       → Desactivar slot
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.middleware.auth_middleware import get_current_user, require_role
from app.services import inventory_service as svc
from app.schemas.inventory import (
    AddInventarioRequest, UpdateInventarioRequest, ReponerInventarioRequest,
    InventarioItemResponse, InventarioMaquinaResponse,
)

router = APIRouter()


@router.get(
    "/{maquina_id}",
    response_model=InventarioMaquinaResponse,
    summary="Ver inventario de una máquina",
)
async def get_inventario(
    maquina_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    items = await svc.get_inventario_maquina(maquina_id, db)
    resumen = await svc.build_resumen(items)
    return InventarioMaquinaResponse(
        maquina_id=maquina_id,
        items=[InventarioItemResponse.model_validate(i) for i in items],
        **resumen,
    )


@router.post(
    "/{maquina_id}/items",
    response_model=InventarioItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar producto a slot (operador/admin)",
)
async def add_item(
    maquina_id: UUID,
    data: AddInventarioRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("operador", "admin")),
):
    item = await svc.add_item(maquina_id, data, db)
    return InventarioItemResponse.model_validate(item)


@router.patch(
    "/{maquina_id}/items/{item_id}",
    response_model=InventarioItemResponse,
    summary="Actualizar configuración de slot",
)
async def update_item(
    maquina_id: UUID,
    item_id: UUID,
    data: UpdateInventarioRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("operador", "admin")),
):
    item = await svc.get_item(item_id, db)
    if not item or item.maquina_id != maquina_id:
        raise HTTPException(status_code=404, detail="Slot no encontrado en esta máquina")
    item = await svc.update_item(item, data, db)
    return InventarioItemResponse.model_validate(item)


@router.post(
    "/{maquina_id}/items/{item_id}/reponer",
    response_model=InventarioItemResponse,
    summary="Reponer stock de un slot",
)
async def reponer_stock(
    maquina_id: UUID,
    item_id: UUID,
    data: ReponerInventarioRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("operador", "admin")),
):
    item = await svc.get_item(item_id, db)
    if not item or item.maquina_id != maquina_id:
        raise HTTPException(status_code=404, detail="Slot no encontrado en esta máquina")
    item = await svc.reponer(item, data.cantidad, db)
    return InventarioItemResponse.model_validate(item)


@router.delete(
    "/{maquina_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar slot",
)
async def deactivate_item(
    maquina_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("operador", "admin")),
):
    item = await svc.get_item(item_id, db)
    if not item or item.maquina_id != maquina_id:
        raise HTTPException(status_code=404, detail="Slot no encontrado en esta máquina")
    await svc.update_item(item, UpdateInventarioRequest(activo=False), db)
