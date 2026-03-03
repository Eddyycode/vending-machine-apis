"""
models/product.py — SQLAlchemy ORM model para Categoria y Producto.

Tablas (schema exacto de Supabase):
  categorias_producto: id, nombre, descripcion, icono_url, activa
  productos: id, categoria_id, nombre, descripcion, codigo_barras, marca,
             imagen_url, precio_base, activo, created_at, updated_at
"""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Categoria(Base):
    __tablename__ = "categorias_producto"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    icono_url   = Column(Text)
    activa      = Column(Boolean, nullable=False, default=True)

    productos = relationship("Producto", back_populates="categoria")


class Producto(Base):
    __tablename__ = "productos"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoria_id  = Column(Integer, ForeignKey("categorias_producto.id"), nullable=False)
    nombre        = Column(String(200), nullable=False)
    descripcion   = Column(Text)
    codigo_barras = Column(String(50))
    marca         = Column(String(100))
    imagen_url    = Column(Text)
    precio_base   = Column(Numeric(10, 2), nullable=False)    # Nombre exacto en Supabase
    activo        = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    categoria  = relationship("Categoria", back_populates="productos")
    inventario = relationship("InventarioMaquina", back_populates="producto")
