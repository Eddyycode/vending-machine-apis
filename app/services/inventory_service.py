"""
services/inventory_service.py — Lógica de negocio para InventarioMaquina.
Usa selectinload anidado para evitar lazy-load (MissingGreenlet) en serialización Pydantic.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventarioMaquina
from app.models.product import Producto
from app.schemas.inventory import AddInventarioRequest, UpdateInventarioRequest


def _opts():
    """Eager-load anidado: producto → categoria."""
    return selectinload(InventarioMaquina.producto).selectinload(Producto.categoria)


async def get_inventario_maquina(maquina_id: UUID, db: AsyncSession) -> list[InventarioMaquina]:
    result = await db.execute(
        select(InventarioMaquina)
        .options(_opts())
        .where(InventarioMaquina.maquina_id == maquina_id)
        .order_by(InventarioMaquina.slot_numero)
    )
    return list(result.scalars().all())


async def get_item(item_id: UUID, db: AsyncSession) -> InventarioMaquina | None:
    result = await db.execute(
        select(InventarioMaquina)
        .options(_opts())
        .where(InventarioMaquina.id == item_id)
    )
    return result.scalar_one_or_none()


async def add_item(maquina_id: UUID, data: AddInventarioRequest, db: AsyncSession) -> InventarioMaquina:
    item = InventarioMaquina(maquina_id=maquina_id, **data.model_dump())
    db.add(item)
    await db.flush()
    result = await db.execute(
        select(InventarioMaquina).options(_opts()).where(InventarioMaquina.id == item.id)
    )
    return result.scalar_one()


async def update_item(
    item: InventarioMaquina,
    data: UpdateInventarioRequest,
    db: AsyncSession,
) -> InventarioMaquina:
    changes = data.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(item, field, value)
    db.add(item)
    await db.flush()
    result = await db.execute(
        select(InventarioMaquina).options(_opts()).where(InventarioMaquina.id == item.id)
    )
    return result.scalar_one()


async def reponer(item: InventarioMaquina, cantidad: int, db: AsyncSession) -> InventarioMaquina:
    """Suma unidades al slot, sin superar cantidad_maxima."""
    nueva = min(item.cantidad_actual + cantidad, item.cantidad_maxima)
    item.cantidad_actual = nueva
    db.add(item)
    await db.flush()
    result = await db.execute(
        select(InventarioMaquina).options(_opts()).where(InventarioMaquina.id == item.id)
    )
    return result.scalar_one()


async def build_resumen(items: list[InventarioMaquina]) -> dict:
    total     = len(items)
    vacios    = sum(1 for i in items if i.cantidad_actual == 0)
    con_stock = total - vacios
    return {"total_slots": total, "slots_vacios": vacios, "slots_con_stock": con_stock}
