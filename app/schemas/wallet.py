"""
schemas/wallet.py — Pydantic DTOs para Wallet, MetodoPago y Recargas.
Columnas mapeadas exactamente con el schema de Supabase.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID


# ─── TARJETAS DE DÉBITO ───────────────────────────────────────────────────────

class AgregarTarjetaRequest(BaseModel):
    """
    En producción, el frontend tokeniza la tarjeta con Stripe.js/PayPal SDK.
    Solo enviamos el token al backend — NUNCA datos reales de tarjeta.
    """
    tipo:              str = Field(default="debito", pattern="^(debito|credito)$")
    marca:             str = Field(examples=["visa", "mastercard"])
    ultimos_cuatro:    str = Field(min_length=4, max_length=4, pattern="^[0-9]{4}$")
    token_procesador:  Optional[str] = None
    es_predeterminado: bool = False


class TarjetaResponse(BaseModel):
    id:                UUID
    tipo:              str
    marca:             Optional[str]
    ultimos_4_digitos: str
    es_principal:      bool
    activo:            bool
    created_at:        datetime

    model_config = {"from_attributes": True}


# ─── RECARGAS ─────────────────────────────────────────────────────────────────

class RecargarWalletRequest(BaseModel):
    monto:          Decimal = Field(gt=0, le=50000, description="Monto a recargar en MXN")
    metodo_pago_id: Optional[UUID] = None


class RecargaResponse(BaseModel):
    id:                 UUID
    monto:              Decimal
    estado:             str
    referencia_externa: Optional[str]
    meta_info:          Optional[Any]
    created_at:         datetime

    model_config = {"from_attributes": True}


# ─── WALLET ───────────────────────────────────────────────────────────────────

class WalletDetalleResponse(BaseModel):
    id:         UUID
    balance:    Decimal
    moneda:     str
    activa:     bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WalletHistorialResponse(BaseModel):
    wallet:          WalletDetalleResponse
    recargas:        list[RecargaResponse]
    total_recargado: Decimal
