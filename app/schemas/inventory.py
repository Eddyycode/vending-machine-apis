"""
schemas/inventory.py — Pydantic DTOs para InventarioMaquina.
Schema exacto de Supabase: usa slot_numero y precio_venta.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.product import ProductoResponse


# ─── REQUESTS ─────────────────────────────────────────────────────────────────

class AddInventarioRequest(BaseModel):
    producto_id:     UUID
    slot_numero:     int            = Field(ge=1, le=500)
    cantidad_actual: int            = Field(default=0, ge=0)
    cantidad_maxima: int            = Field(default=10, ge=1, le=500)
    precio_venta:    float          = Field(gt=0)
    fecha_caducidad: Optional[date] = None
    costo_unitario:  Optional[float] = None


class UpdateInventarioRequest(BaseModel):
    cantidad_actual: Optional[int]   = Field(default=None, ge=0)
    cantidad_maxima: Optional[int]   = Field(default=None, ge=1, le=500)
    precio_venta:    Optional[float] = Field(default=None, gt=0)
    fecha_caducidad: Optional[date]  = None
    costo_unitario:  Optional[float] = None
    activo:          Optional[bool]  = None


class ReponerInventarioRequest(BaseModel):
    cantidad: int = Field(gt=0, description="Unidades a reponer")


# ─── RESPONSES ────────────────────────────────────────────────────────────────

class InventarioItemResponse(BaseModel):
    id:              UUID
    maquina_id:      UUID
    slot_numero:     int
    cantidad_actual: int
    cantidad_maxima: int
    precio_venta:    float
    fecha_caducidad: Optional[date]  = None
    costo_unitario:  Optional[float] = None
    activo:          bool
    updated_at:      datetime
    producto:        Optional[ProductoResponse] = None
    model_config = {"from_attributes": True}


class InventarioMaquinaResponse(BaseModel):
    maquina_id:      UUID
    items:           list[InventarioItemResponse]
    total_slots:     int
    slots_vacios:    int
    slots_con_stock: int
