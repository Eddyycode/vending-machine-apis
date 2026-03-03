"""
models/promotion.py — SQLAlchemy ORM model para Promocion.

Tabla: promociones (schema exacto de Supabase — 16 columnas)
  id, operador_id, nombre, descripcion, tipo, valor, aplica_a,
  referencia_id, monto_minimo, usos_maximos, usos_actuales,
  fecha_inicio, fecha_fin, activa, codigo_cupon, created_at
"""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Promocion(Base):
    __tablename__ = "promociones"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operador_id   = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nombre        = Column(String(200), nullable=False)
    descripcion   = Column(Text)
    # tipo: 'porcentaje', 'monto_fijo', '2x1', 'producto_gratis'
    tipo          = Column(String(30), nullable=False)
    valor         = Column(Numeric(10, 2), nullable=False)
    # aplica_a: 'producto', 'maquina', 'categoria', 'global'
    aplica_a      = Column(String(20), nullable=False, default="producto")
    referencia_id = Column(UUID(as_uuid=True))               # ID del producto/maquina/categoria
    monto_minimo  = Column(Numeric(10, 2), default=0)
    usos_maximos  = Column(Integer)
    usos_actuales = Column(Integer, nullable=False, default=0)
    fecha_inicio  = Column(DateTime(timezone=True), nullable=False)
    fecha_fin     = Column(DateTime(timezone=True), nullable=False)
    activa        = Column(Boolean, nullable=False, default=True)
    codigo_cupon  = Column(String(50), unique=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    operador = relationship("Usuario", foreign_keys=[operador_id])
