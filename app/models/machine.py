"""
models/machine.py — SQLAlchemy ORM model para MaquinaExpendedora.

Tabla: maquinas (schema exacto de Supabase)
  id, operador_id, ubicacion_id, nombre, codigo_serial, modelo,
  capacidad_total, estado, ultima_sincronizacion, imagen_url, notas,
  created_at, updated_at
"""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class MaquinaExpendedora(Base):
    __tablename__ = "maquinas"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operador_id           = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    ubicacion_id          = Column(UUID(as_uuid=True), ForeignKey("ubicaciones.id"), nullable=False)
    nombre                = Column(String(150), nullable=False)
    codigo_serial         = Column(String(100), unique=True, nullable=False)
    modelo                = Column(String(100))
    capacidad_total       = Column(Integer, nullable=False, default=0)
    # estado: 'activa', 'mantenimiento', 'inactiva', 'fuera_de_servicio'
    estado                = Column(String(20), nullable=False, default="activa")
    ultima_sincronizacion = Column(DateTime(timezone=True))
    imagen_url            = Column(Text)
    notas                 = Column(Text)
    created_at            = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at            = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    operador   = relationship("Usuario", foreign_keys=[operador_id])
    ubicacion  = relationship("Ubicacion", foreign_keys=[ubicacion_id])
    inventario = relationship("InventarioMaquina", back_populates="maquina", cascade="all, delete-orphan")
