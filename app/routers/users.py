"""
routers/users.py — Endpoints del perfil de usuario autenticado.

GET  /users/me         → Retorna el perfil del usuario logueado
PATCH /users/me        → Actualiza nombre, teléfono, avatar
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.database import get_db
from app.models.user import Usuario
from app.schemas.user import UserResponse
from app.middleware.auth_middleware import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    nombre:    Optional[str] = None
    apellidos: Optional[str] = None
    telefono:  Optional[str] = None
    avatar_url: Optional[str] = None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Mi perfil",
)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    """Retorna el perfil completo del usuario autenticado, incluyendo rol y wallet."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Actualizar mi perfil",
)
async def update_me(
    data: UpdateProfileRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza campos del perfil. Solo los campos enviados se modifican."""
    changes = data.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    for field, value in changes.items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user, ["rol", "wallet"])

    return UserResponse.model_validate(current_user)
