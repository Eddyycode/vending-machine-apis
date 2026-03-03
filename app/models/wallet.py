"""
models/wallet.py — SQLAlchemy ORM models para MetodoPago y RecargaWallet.

Columnas mapeadas con los nombres EXACTOS del schema de Supabase:
  metodos_pago:    id, usuario_id, tipo, marca, ultimos_4_digitos,
                   token_procesador, es_principal, activo, created_at
  recargas_wallet: id, wallet_id, metodo_pago_id, monto, estado,
                   referencia_externa, metadata, created_at, updated_at
"""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, JSON,
    Numeric, String, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class MetodoPago(Base):
    __tablename__ = "metodos_pago"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id        = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tipo              = Column(String(20), nullable=False, default="debito")  # 'debito' | 'credito'
    marca             = Column(String(20))                                    # 'visa', 'mastercard'
    ultimos_4_digitos = Column(String(4), nullable=False)                     # '4242'
    token_procesador  = Column(String(255))                                   # Stripe/PayPal token
    es_principal      = Column(Boolean, nullable=False, default=False)        # tarjeta predeterminada
    activo            = Column(Boolean, nullable=False, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", backref="metodos_pago")


class RecargaWallet(Base):
    __tablename__ = "recargas_wallet"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id          = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    metodo_pago_id     = Column(UUID(as_uuid=True), ForeignKey("metodos_pago.id"), nullable=True)
    monto              = Column(Numeric(12, 2), nullable=False)
    # Estado: 'pendiente', 'completado', 'fallido', 'reembolsado'
    estado             = Column(String(20), nullable=False, default="completado")
    # referencia_externa: charge_id de Stripe/PayPal. Simulado por ahora.
    referencia_externa = Column(String(255))
    # metadata es palabra reservada en SQLAlchemy, usamos meta_info como atributo
    meta_info          = Column("metadata", JSON)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
