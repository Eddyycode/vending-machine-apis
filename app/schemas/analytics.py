"""
schemas/analytics.py — Pydantic DTOs para Alertas, Mermas y Dashboard.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


# ─── ALERTAS ──────────────────────────────────────────────────────────────────

class AlertaResponse(BaseModel):
    id:          UUID
    maquina_id:  UUID
    producto_id: UUID
    tipo:        str
    mensaje:     Optional[str] = None
    resuelta:    bool
    created_at:  datetime
    model_config = {"from_attributes": True}


# ─── MERMAS ───────────────────────────────────────────────────────────────────

class RegistrarMermaRequest(BaseModel):
    maquina_id:  UUID
    producto_id: UUID
    cantidad:    int  = Field(gt=0)
    motivo:      str  = Field(default="otro", pattern="^(vencimiento|dano|robo|otro)$")


class MermaResponse(BaseModel):
    id:             UUID
    maquina_id:     UUID
    producto_id:    UUID
    cantidad:       int
    motivo:         str
    registrado_por: Optional[UUID] = None
    created_at:     datetime
    model_config = {"from_attributes": True}


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    total_ventas_hoy:        float
    total_transacciones_hoy: int
    maquinas_activas:        int
    maquinas_sin_stock:      int
    alertas_pendientes:      int
    mermas_mes:              int
