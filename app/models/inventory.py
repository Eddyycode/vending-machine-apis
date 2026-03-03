"""
models/inventory.py — SQLAlchemy ORM model para InventarioMaquina e HistorialInventario.

Tablas (schema exacto de Supabase):
  inventario_maquina:   id, maquina_id, producto_id, slot_numero, cantidad_actual,
                        cantidad_maxima, precio_venta, fecha_caducidad, costo_unitario,
                        activo, created_at, updated_at
  historial_inventario: id (BIGSERIAL), inventario_id, maquina_id, producto_id,
                        tipo_movimiento, cantidad_anterior, cantidad_nueva, delta (GENERATED),
                        operado_por, transaccion_id, notas, created_at
"""
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime,
    ForeignKey, Integer, Numeric, SmallInteger, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class InventarioMaquina(Base):
    __tablename__ = "inventario_maquina"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    maquina_id      = Column(UUID(as_uuid=True), ForeignKey("maquinas.id", ondelete="CASCADE"), nullable=False)
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    slot_numero     = Column(SmallInteger, nullable=False)           # Número de slot (1, 2, 3…)
    cantidad_actual = Column(SmallInteger, nullable=False, default=0)
    cantidad_maxima = Column(SmallInteger, nullable=False, default=0)
    precio_venta    = Column(Numeric(10, 2), nullable=False)         # Precio en esta máquina
    fecha_caducidad = Column(Date)
    costo_unitario  = Column(Numeric(10, 2))
    activo          = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    maquina  = relationship("MaquinaExpendedora", back_populates="inventario")
    producto = relationship("Producto", back_populates="inventario")
    historial = relationship("HistorialInventario", back_populates="inventario_item", cascade="all, delete-orphan")


class HistorialInventario(Base):
    """Log inmutable de movimientos de stock — BIGSERIAL PK, nunca se borra."""
    __tablename__ = "historial_inventario"

    id                = Column(BigInteger, primary_key=True, autoincrement=True)
    inventario_id     = Column(UUID(as_uuid=True), ForeignKey("inventario_maquina.id"), nullable=False)
    maquina_id        = Column(UUID(as_uuid=True), ForeignKey("maquinas.id"), nullable=False)
    producto_id       = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    # tipo_movimiento: 'venta','reabastecimiento','ajuste','merma','caducidad','ajuste_baja','ajuste_alta'
    tipo_movimiento   = Column(String(30), nullable=False)
    cantidad_anterior = Column(SmallInteger, nullable=False)
    cantidad_nueva    = Column(SmallInteger, nullable=False)
    # delta es columna GENERATED en Supabase, no la definimos aquí pero podemos leerla
    operado_por       = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    transaccion_id    = Column(UUID(as_uuid=True))                   # FK a transacciones (opcional)
    notas             = Column(Text)
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    inventario_item = relationship("InventarioMaquina", back_populates="historial")
    maquina  = relationship("MaquinaExpendedora", foreign_keys=[maquina_id])
    producto = relationship("Producto", foreign_keys=[producto_id])
