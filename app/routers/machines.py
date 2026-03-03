"""
routers/machines.py — Endpoints de MaquinaExpendedora y Ubicaciones.

GET    /machines/              → Listar máquinas (todos los auth)
POST   /machines/              → Crear máquina (operador/admin)
GET    /machines/{id}          → Detalle + inventario resumen
PATCH  /machines/{id}          → Actualizar (operador/admin)
DELETE /machines/{id}          → Desactivar (admin)
GET    /machines/ubicaciones/  → Listar ubicaciones disponibles
POST   /machines/ubicaciones/  → Crear ubicación (operador/admin)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.models.ubicacion import Ubicacion
from app.middleware.auth_middleware import get_current_user, require_role
from app.services import machine_service as svc
from app.schemas.machine import (
    CreateMaquinaRequest, UpdateMaquinaRequest,
    MaquinaResponse, MaquinaListResponse,
    CreateUbicacionRequest, UbicacionResponse,
)

router = APIRouter()


# ─── UBICACIONES ──────────────────────────────────────────────────────────────

@router.get(
    "/ubicaciones/",
    response_model=list[UbicacionResponse],
    summary="Listar ubicaciones disponibles",
)
async def list_ubicaciones(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Ubicacion).where(Ubicacion.activa == True).order_by(Ubicacion.ciudad))
    locs = result.scalars().all()
    return [UbicacionResponse.model_validate(u) for u in locs]


@router.post(
    "/ubicaciones/",
    response_model=UbicacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ubicación (operador/admin)",
)
async def create_ubicacion(
    data: CreateUbicacionRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("operador", "admin")),
):
    ubicacion = Ubicacion(**data.model_dump())
    db.add(ubicacion)
    await db.flush()
    await db.refresh(ubicacion)
    return UbicacionResponse.model_validate(ubicacion)


# ─── MÁQUINAS ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=MaquinaListResponse,
    summary="Listar máquinas expendedoras",
)
async def list_maquinas(
    solo_activas: bool = True,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    items, total = await svc.list_maquinas(db, solo_activas)
    return MaquinaListResponse(
        total=total,
        maquinas=[MaquinaResponse.model_validate(m) for m in items],
    )


@router.post(
    "/",
    response_model=MaquinaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear máquina (operador/admin)",
)
async def create_maquina(
    data: CreateMaquinaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role("operador", "admin")),
):
    maquina = await svc.create_maquina(data, current_user.id, db)
    return MaquinaResponse.model_validate(maquina)


@router.get(
    "/{maquina_id}",
    response_model=MaquinaResponse,
    summary="Detalle de máquina",
)
async def get_maquina(
    maquina_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    maquina = await svc.get_maquina(maquina_id, db)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    return MaquinaResponse.model_validate(maquina)


@router.patch(
    "/{maquina_id}",
    response_model=MaquinaResponse,
    summary="Actualizar máquina",
)
async def update_maquina(
    maquina_id: UUID,
    data: UpdateMaquinaRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("operador", "admin")),
):
    maquina = await svc.get_maquina(maquina_id, db)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    maquina = await svc.update_maquina(maquina, data, db)
    return MaquinaResponse.model_validate(maquina)


@router.delete(
    "/{maquina_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar máquina (admin)",
)
async def delete_maquina(
    maquina_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin")),
):
    maquina = await svc.get_maquina(maquina_id, db)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    await svc.delete_maquina(maquina, db)
