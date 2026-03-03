"""
schemas/transaction.py — Pydantic DTOs para Transaccion.
Schema real de Supabase: 1 transacción = 1 producto (no hay tabla de detalle).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID


# ─── RESPONSE ─────────────────────────────────────────────────────────────────

class TransaccionResponse(BaseModel):
    id:                 UUID
    cliente_id:         UUID
    maquina_id:         UUID
    inventario_id:      UUID
    producto_id:        UUID
    wallet_id:          UUID
    promocion_id:       Optional[UUID]  = None
    cantidad:           int
    precio_unitario:    float
    descuento_aplicado: float
    total:              float
    estado:             str
    medio_pago:         str
    created_at:         datetime
    model_config = {"from_attributes": True}


class TransaccionListResponse(BaseModel):
    total:         int
    transacciones: list[TransaccionResponse]
