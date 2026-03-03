"""
services/machine_service.py — Lógica de negocio para MaquinaExpendedora.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import MaquinaExpendedora
from app.schemas.machine import CreateMaquinaRequest, UpdateMaquinaRequest


async def list_maquinas(db: AsyncSession, solo_activas: bool = True) -> tuple[list[MaquinaExpendedora], int]:
    q = (
        select(MaquinaExpendedora)
        .options(selectinload(MaquinaExpendedora.ubicacion))
    )
    if solo_activas:
        q = q.where(MaquinaExpendedora.estado == "activa")
    q = q.order_by(MaquinaExpendedora.created_at.desc())
    result = await db.execute(q)
    items = list(result.scalars().all())
    return items, len(items)


async def get_maquina(maquina_id: UUID, db: AsyncSession) -> MaquinaExpendedora | None:
    result = await db.execute(
        select(MaquinaExpendedora)
        .options(selectinload(MaquinaExpendedora.ubicacion))
        .where(MaquinaExpendedora.id == maquina_id)
    )
    return result.scalar_one_or_none()


async def create_maquina(
    data: CreateMaquinaRequest,
    operador_id: UUID,
    db: AsyncSession,
) -> MaquinaExpendedora:
    maquina = MaquinaExpendedora(
        operador_id=operador_id,
        **data.model_dump(),
    )
    db.add(maquina)
    await db.flush()
    await db.refresh(maquina, ["ubicacion"])
    return maquina


async def update_maquina(
    maquina: MaquinaExpendedora,
    data: UpdateMaquinaRequest,
    db: AsyncSession,
) -> MaquinaExpendedora:
    changes = data.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(maquina, field, value)
    db.add(maquina)
    await db.flush()
    await db.refresh(maquina, ["ubicacion"])
    return maquina


async def delete_maquina(maquina: MaquinaExpendedora, db: AsyncSession) -> None:
    """Soft-delete: cambia estado a 'inactiva'."""
    maquina.estado = "inactiva"
    db.add(maquina)
    await db.flush()
