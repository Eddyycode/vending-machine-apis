"""
models/ubicacion.py — SQLAlchemy ORM model para Ubicacion.

Tabla: ubicaciones (schema exacto de Supabase)
  id, nombre, direccion, ciudad, estado, codigo_postal, pais,
  latitud, longitud, activa, created_at
"""
from sqlalchemy import (
    Boolean, Column, DateTime, Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Ubicacion(Base):
    __tablename__ = "ubicaciones"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre        = Column(String(200), nullable=False)         # "Plaza Galerías GDL - PB"
    direccion     = Column(Text, nullable=False)
    ciudad        = Column(String(100), nullable=False)
    estado        = Column(String(100), nullable=False)         # Estado/provincia
    codigo_postal = Column(String(5))
    pais          = Column(String(2), nullable=False, default="MX")
    latitud       = Column(Numeric(10, 7))
    longitud      = Column(Numeric(10, 7))
    activa        = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    maquinas = relationship("MaquinaExpendedora", back_populates="ubicacion")
