"""
services/product_service.py — Lógica de negocio para Categoria y Producto.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Producto, Categoria
from app.schemas.product import CreateProductoRequest, UpdateProductoRequest


async def list_categorias(db: AsyncSession) -> list[Categoria]:
    result = await db.execute(select(Categoria).where(Categoria.activa == True))
    return list(result.scalars().all())


async def list_productos(
    db: AsyncSession,
    solo_activos: bool = True,
    categoria_id: int | None = None,
) -> tuple[list[Producto], int]:
    q = select(Producto).options(selectinload(Producto.categoria))
    if solo_activos:
        q = q.where(Producto.activo == True)
    if categoria_id:
        q = q.where(Producto.categoria_id == categoria_id)
    q = q.order_by(Producto.nombre)
    result = await db.execute(q)
    items = list(result.scalars().all())
    return items, len(items)


async def get_producto(producto_id: UUID, db: AsyncSession) -> Producto | None:
    result = await db.execute(
        select(Producto)
        .options(selectinload(Producto.categoria))
        .where(Producto.id == producto_id)
    )
    return result.scalar_one_or_none()


async def create_producto(data: CreateProductoRequest, db: AsyncSession) -> Producto:
    producto = Producto(**data.model_dump())
    db.add(producto)
    await db.flush()
    await db.refresh(producto, ["categoria"])
    return producto


async def update_producto(
    producto: Producto,
    data: UpdateProductoRequest,
    db: AsyncSession,
) -> Producto:
    changes = data.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(producto, field, value)
    db.add(producto)
    await db.flush()
    await db.refresh(producto, ["categoria"])
    return producto


async def delete_producto(producto: Producto, db: AsyncSession) -> None:
    """Soft-delete."""
    producto.activo = False
    db.add(producto)
    await db.flush()
