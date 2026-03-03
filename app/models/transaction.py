"""
models/transaction.py — SQLAlchemy ORM model para Transaccion.

Tabla: transacciones (schema exacto de Supabase)
  1 transacción = 1 producto comprado (no hay tabla de detalle separada en Supabase)

  id, cliente_id, maquina_id, inventario_id, producto_id, wallet_id,
  promocion_id, cantidad, precio_unitario, descuento_aplicado, total,
  estado, medio_pago, metadata, created_at
"""
from sqlalchemy import (
    Column, DateTime, ForeignKey, Numeric,
    SmallInteger, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Transaccion(Base):
    __tablename__ = "transacciones"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id         = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    maquina_id         = Column(UUID(as_uuid=True), ForeignKey("maquinas.id"), nullable=False)
    inventario_id      = Column(UUID(as_uuid=True), ForeignKey("inventario_maquina.id"), nullable=False)
    producto_id        = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    wallet_id          = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    promocion_id       = Column(UUID(as_uuid=True), ForeignKey("promociones.id", ondelete="SET NULL"), nullable=True)
    cantidad           = Column(SmallInteger, nullable=False, default=1)
    precio_unitario    = Column(Numeric(10, 2), nullable=False)
    descuento_aplicado = Column(Numeric(10, 2), nullable=False, default=0.00)
    total              = Column(Numeric(10, 2), nullable=False)
    # estado: 'completada', 'cancelada', 'reembolsada'
    estado             = Column(String(20), nullable=False, default="completada")
    medio_pago         = Column(String(20), nullable=False, default="wallet")
    meta_info          = Column("metadata", JSONB)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cliente   = relationship("Usuario", foreign_keys=[cliente_id])
    maquina   = relationship("MaquinaExpendedora", foreign_keys=[maquina_id])
    inventario = relationship("InventarioMaquina", foreign_keys=[inventario_id])
    producto  = relationship("Producto", foreign_keys=[producto_id])
    wallet    = relationship("Wallet", foreign_keys=[wallet_id])
    promocion = relationship("Promocion", foreign_keys=[promocion_id])
