"""
schemas/product.py — Pydantic DTOs para Categoria y Producto.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


# ─── CATEGORIA ────────────────────────────────────────────────────────────────

class CategoriaResponse(BaseModel):
    id:          int
    nombre:      str
    descripcion: Optional[str] = None
    activa:      bool
    model_config = {"from_attributes": True}


# ─── REQUESTS ─────────────────────────────────────────────────────────────────

class CreateProductoRequest(BaseModel):
    nombre:        str           = Field(min_length=2, max_length=120)
    descripcion:   Optional[str] = None
    precio:        float         = Field(gt=0)
    categoria_id:  Optional[int] = None
    imagen_url:    Optional[str] = None
    codigo_barras: Optional[str] = Field(default=None, max_length=50)


class UpdateProductoRequest(BaseModel):
    nombre:        Optional[str]   = None
    descripcion:   Optional[str]   = None
    precio:        Optional[float] = Field(default=None, gt=0)
    categoria_id:  Optional[int]   = None
    imagen_url:    Optional[str]   = None
    codigo_barras: Optional[str]   = None
    activo:        Optional[bool]  = None


# ─── RESPONSES ────────────────────────────────────────────────────────────────

class ProductoResponse(BaseModel):
    id:            UUID
    nombre:        str
    descripcion:   Optional[str]  = None
    precio_base:   float                    # Nombre exacto en Supabase
    marca:         Optional[str]  = None
    imagen_url:    Optional[str]  = None
    codigo_barras: Optional[str]  = None
    activo:        bool
    categoria:     Optional[CategoriaResponse] = None
    created_at:    datetime
    updated_at:    datetime
    model_config = {"from_attributes": True}


class ProductoListResponse(BaseModel):
    total:     int
    productos: list[ProductoResponse]
