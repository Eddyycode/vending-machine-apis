"""
routers/products.py — Endpoints del catálogo de productos.

GET    /products/             → Listar productos
POST   /products/             → Crear producto (admin)
GET    /products/{id}         → Detalle de producto
PATCH  /products/{id}         → Actualizar producto (admin)
DELETE /products/{id}         → Desactivar producto (admin)
GET    /products/categorias   → Listar categorías
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.middleware.auth_middleware import get_current_user, require_role
from app.services import product_service as svc
from app.schemas.product import (
    CreateProductoRequest, UpdateProductoRequest,
    ProductoResponse, ProductoListResponse, CategoriaResponse,
)

router = APIRouter()


@router.get(
    "/categorias",
    response_model=list[CategoriaResponse],
    summary="Listar categorías",
)
async def list_categorias(db: AsyncSession = Depends(get_db)):
    cats = await svc.list_categorias(db)
    return [CategoriaResponse.model_validate(c) for c in cats]


@router.get(
    "/",
    response_model=ProductoListResponse,
    summary="Listar productos",
)
async def list_productos(
    solo_activos: bool = True,
    categoria_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    items, total = await svc.list_productos(db, solo_activos, categoria_id)
    return ProductoListResponse(
        total=total,
        productos=[ProductoResponse.model_validate(p) for p in items],
    )


@router.post(
    "/",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto (admin)",
)
async def create_producto(
    data: CreateProductoRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin", "operador")),
):
    producto = await svc.create_producto(data, db)
    return ProductoResponse.model_validate(producto)


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Detalle de producto",
)
async def get_producto(
    producto_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    producto = await svc.get_producto(producto_id, db)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductoResponse.model_validate(producto)


@router.patch(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Actualizar producto",
)
async def update_producto(
    producto_id: UUID,
    data: UpdateProductoRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin", "operador")),
):
    producto = await svc.get_producto(producto_id, db)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    producto = await svc.update_producto(producto, data, db)
    return ProductoResponse.model_validate(producto)


@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar producto (admin)",
)
async def delete_producto(
    producto_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin")),
):
    producto = await svc.get_producto(producto_id, db)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    await svc.delete_producto(producto, db)
