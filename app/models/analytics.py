"""
models/analytics.py — SQLAlchemy ORM models para AlertaStock, Merma y PrediccionDemanda.

Tablas (schema exacto de Supabase):
  alertas_stock:       id, maquina_id, inventario_id, operador_id, tipo, nivel_urgencia,
                       cantidad_umbral, dias_para_caducidad, mensaje, leida, resuelta,
                       fecha_resolucion, created_at
  mermas:              id, maquina_id, inventario_id, producto_id, operador_id, cantidad,
                       motivo, costo_unitario, costo_total (GENERATED), fecha_caducidad,
                       notas, evidencia_url, created_at
  predicciones_demanda: id, maquina_id, producto_id, fecha_prediccion, unidades_predichas,
                        dias_hasta_agotamiento, confianza, modelo_version,
                        features_snapshot, created_at
"""
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, ForeignKey,
    Numeric, SmallInteger, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class AlertaStock(Base):
    __tablename__ = "alertas_stock"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    maquina_id          = Column(UUID(as_uuid=True), ForeignKey("maquinas.id"), nullable=False)
    inventario_id       = Column(UUID(as_uuid=True), ForeignKey("inventario_maquina.id"), nullable=False)
    operador_id         = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    # tipo: 'stock_bajo', 'stock_critico', 'agotado', 'caducidad_proxima'
    tipo                = Column(String(30), nullable=False)
    # nivel_urgencia: 'bajo', 'medio', 'alto', 'critico'
    nivel_urgencia      = Column(String(10), nullable=False, default="medio")
    cantidad_umbral     = Column(SmallInteger)
    dias_para_caducidad = Column(SmallInteger)
    mensaje             = Column(Text, nullable=False)
    leida               = Column(Boolean, nullable=False, default=False)
    resuelta            = Column(Boolean, nullable=False, default=False)
    fecha_resolucion    = Column(DateTime(timezone=True))
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    maquina    = relationship("MaquinaExpendedora", foreign_keys=[maquina_id])
    inventario = relationship("InventarioMaquina", foreign_keys=[inventario_id])
    operador   = relationship("Usuario", foreign_keys=[operador_id])


class Merma(Base):
    __tablename__ = "mermas"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    maquina_id      = Column(UUID(as_uuid=True), ForeignKey("maquinas.id"), nullable=False)
    inventario_id   = Column(UUID(as_uuid=True), ForeignKey("inventario_maquina.id"), nullable=False)
    producto_id     = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    operador_id     = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    cantidad        = Column(SmallInteger, nullable=False)
    # motivo: 'caducidad', 'daño', 'robo', 'error_reabastecimiento'
    motivo          = Column(String(30), nullable=False)
    costo_unitario  = Column(Numeric(10, 2))
    # costo_total es GENERATED en Supabase (cantidad * costo_unitario) — solo lectura
    fecha_caducidad = Column(Date)
    notas           = Column(Text)
    evidencia_url   = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    maquina    = relationship("MaquinaExpendedora", foreign_keys=[maquina_id])
    inventario = relationship("InventarioMaquina", foreign_keys=[inventario_id])
    producto   = relationship("Producto", foreign_keys=[producto_id])
    operador   = relationship("Usuario", foreign_keys=[operador_id])


class PrediccionDemanda(Base):
    __tablename__ = "predicciones_demanda"

    id                     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    maquina_id             = Column(UUID(as_uuid=True), ForeignKey("maquinas.id"), nullable=False)
    producto_id            = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False)
    fecha_prediccion       = Column(Date, nullable=False)
    unidades_predichas     = Column(Numeric(8, 2), nullable=False)
    dias_hasta_agotamiento = Column(SmallInteger)
    confianza              = Column(Numeric(5, 4))              # 0.0000 – 1.0000
    modelo_version         = Column(String(50))
    features_snapshot      = Column(JSONB)                      # Snapshot de features del ML
    created_at             = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    maquina  = relationship("MaquinaExpendedora", foreign_keys=[maquina_id])
    producto = relationship("Producto", foreign_keys=[producto_id])
