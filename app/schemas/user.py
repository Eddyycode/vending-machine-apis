"""
schemas/user.py — Pydantic DTOs para Auth y Usuarios.
"""
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


def _validate_email(v: str) -> str:
    """Validación básica de email sin DNS check — Supabase valida el resto."""
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v.strip()):
        raise ValueError("Invalid email format")
    return v.strip().lower()


# ─── REQUESTS ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:     str = Field(min_length=5)
    password:  str = Field(min_length=8)
    nombre:    str = Field(min_length=1, max_length=100)
    apellidos: Optional[str] = None
    telefono:  Optional[str] = None
    rol:       str = Field(default="cliente", pattern="^(cliente|operador)$")

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email(v)


class LoginRequest(BaseModel):
    email:    str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email(v)


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── RESPONSES ────────────────────────────────────────────────────────────────

class RolResponse(BaseModel):
    id:     int
    nombre: str
    model_config = {"from_attributes": True}


class WalletResponse(BaseModel):
    id:      UUID
    balance: float
    moneda:  str
    activa:  bool
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id:           UUID
    email:        str
    nombre:       str
    apellidos:    Optional[str] = None
    telefono:     Optional[str] = None
    avatar_url:   Optional[str] = None
    activo:       bool
    ultimo_login: Optional[datetime] = None
    created_at:   datetime
    rol:          RolResponse
    wallet:       Optional[WalletResponse] = None
    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int = 3600
    usuario:       UserResponse


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int = 3600


class UpdateProfileRequest(BaseModel):
    nombre:     Optional[str] = None
    apellidos:  Optional[str] = None
    telefono:   Optional[str] = None
    avatar_url: Optional[str] = None
