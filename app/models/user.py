"""
models/user.py — SQLAlchemy ORM models para Rol, Usuario y Wallet.
Mapean directamente a las tablas diseñadas en el schema PostgreSQL.
"""
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Rol(Base):
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(50), nullable=False, unique=True)   # 'cliente','operador','admin'
    descripcion = Column(Text)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuarios    = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_uid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    rol_id       = Column(Integer, ForeignKey("roles.id"), nullable=False)
    nombre       = Column(String(100), nullable=False)
    apellidos    = Column(String(100))
    email        = Column(String(255), nullable=False, unique=True)
    telefono     = Column(String(20))
    avatar_url   = Column(Text)
    activo       = Column(Boolean, nullable=False, default=True)
    ultimo_login = Column(DateTime(timezone=True))
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    rol    = relationship("Rol", back_populates="usuarios")
    wallet = relationship("Wallet", back_populates="usuario", uselist=False)


class Wallet(Base):
    __tablename__ = "wallets"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance    = Column(Numeric(12, 2), nullable=False, default=0.00)
    moneda     = Column(String(3), nullable=False, default="MXN")
    activa     = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    usuario = relationship("Usuario", back_populates="wallet")
