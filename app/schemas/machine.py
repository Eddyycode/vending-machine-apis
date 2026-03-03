"""
schemas/machine.py — Pydantic DTOs para MaquinaExpendedora.
Schema exacto de Supabase: maquinas tiene ubicacion_id y codigo_serial.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


# ─── Ubicacion anidada ────────────────────────────────────────────────────────

class UbicacionBriefResponse(BaseModel):
    id:     UUID
    nombre: str
    ciudad: str
    estado: str
    model_config = {"from_attributes": True}


# ─── REQUESTS ─────────────────────────────────────────────────────────────────

class CreateMaquinaRequest(BaseModel):
    nombre:          str           = Field(min_length=2, max_length=150)
    codigo_serial:   str           = Field(min_length=2, max_length=100)
    ubicacion_id:    UUID
    modelo:          Optional[str] = None
    capacidad_total: int           = Field(default=50, ge=0, le=1000)
    notas:           Optional[str] = None


class UpdateMaquinaRequest(BaseModel):
    nombre:          Optional[str]  = None
    modelo:          Optional[str]  = None
    capacidad_total: Optional[int]  = Field(default=None, ge=0, le=1000)
    estado:          Optional[str]  = Field(default=None, pattern="^(activa|mantenimiento|inactiva|fuera_de_servicio)$")
    ubicacion_id:    Optional[UUID] = None
    imagen_url:      Optional[str]  = None
    notas:           Optional[str]  = None


# ─── RESPONSES ────────────────────────────────────────────────────────────────

class MaquinaResponse(BaseModel):
    id:                    UUID
    nombre:                str
    codigo_serial:         str
    modelo:                Optional[str]     = None
    estado:                str
    capacidad_total:       int
    operador_id:           UUID
    ubicacion_id:          UUID
    ubicacion:             Optional[UbicacionBriefResponse] = None
    imagen_url:            Optional[str]     = None
    notas:                 Optional[str]     = None
    ultima_sincronizacion: Optional[datetime] = None
    created_at:            datetime
    updated_at:            datetime
    model_config = {"from_attributes": True}


class MaquinaListResponse(BaseModel):
    total:    int
    maquinas: list[MaquinaResponse]


# ─── UBICACION ────────────────────────────────────────────────────────────────

class CreateUbicacionRequest(BaseModel):
    nombre:        str           = Field(min_length=3, max_length=200)
    direccion:     str
    ciudad:        str           = Field(min_length=2, max_length=100)
    estado:        str           = Field(min_length=2, max_length=100)
    codigo_postal: Optional[str] = Field(default=None, max_length=5)
    pais:          str           = Field(default="MX", max_length=2)
    latitud:       Optional[float] = None
    longitud:      Optional[float] = None


class UbicacionResponse(BaseModel):
    id:            UUID
    nombre:        str
    direccion:     str
    ciudad:        str
    estado:        str
    codigo_postal: Optional[str]   = None
    pais:          str
    latitud:       Optional[float] = None
    longitud:      Optional[float] = None
    activa:        bool
    created_at:    datetime
    model_config = {"from_attributes": True}
