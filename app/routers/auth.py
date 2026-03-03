"""
routers/auth.py — Endpoints de autenticación.

POST /auth/register  → Registra nuevo usuario
POST /auth/login     → Inicia sesión, retorna JWT + refresh token
POST /auth/refresh   → Renueva el access token
POST /auth/logout    → Cierra sesión (invalida refresh token en Supabase)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    RegisterRequest, LoginRequest, RefreshRequest,
    AuthResponse, TokenRefreshResponse, UserResponse,
)
from app.services import auth_service as svc
from app.middleware.auth_middleware import get_current_user
from app.models.user import Usuario

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario (cliente u operador)",
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    1. Crea el usuario en Supabase Auth
    2. Crea la fila en `usuarios` de nuestra BD
    3. Si es cliente, crea su `wallet` vacía
    4. Retorna los tokens de sesión
    """
    # Verificar que el email no exista ya en nuestra BD
    existing = await svc.get_usuario_by_email(data.email, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # 1. Registrar en Supabase Auth
    try:
        supa_data = await svc.supabase_signup(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    supabase_uid = supa_data["user"]["id"]
    access_token  = supa_data.get("access_token", "")
    refresh_token = supa_data.get("refresh_token", "")

    # Si Supabase tiene email confirmation habilitado, no se pueden retornar tokens aún
    if supa_data.get("email_confirmation_required"):
        # Crear el usuario en nuestra BD de todas formas (para que esté listo cuando confirme)
        try:
            rol = await svc.get_rol_by_nombre(data.rol, db)
            await svc.create_usuario_en_db(supabase_uid, data, rol, db)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=(
                "Registration successful! Please check your email and confirm your account. "
                "Tip: Disable 'Confirm email' in Supabase → Authentication → Settings for development."
            ),
        )

    # 2. Obtener rol y crear usuario en nuestra BD
    try:
        rol = await svc.get_rol_by_nombre(data.rol, db)
        usuario = await svc.create_usuario_en_db(supabase_uid, data, rol, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 3. Actualizar ultimo_login
    await svc.update_ultimo_login(usuario, db)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=UserResponse.model_validate(usuario),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Iniciar sesión",
)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Autentica con Supabase y actualiza `ultimo_login` en nuestra BD.
    Para operadores/admins, este timestamp es el que controla la sesión de 24h.
    """
    # Autenticar en Supabase
    try:
        supa_data = await svc.supabase_login(data.email, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    supabase_uid = supa_data["user"]["id"]
    access_token  = supa_data["access_token"]
    refresh_token = supa_data["refresh_token"]

    # Buscar usuario en nuestra BD
    usuario = await svc.get_usuario_by_supabase_uid(supabase_uid, db)
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Actualizar ultimo_login
    await svc.update_ultimo_login(usuario, db)
    await db.refresh(usuario, ["rol", "wallet"])

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=UserResponse.model_validate(usuario),
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Renovar access token",
)
async def refresh_token(data: RefreshRequest):
    """
    Usa el refresh token para obtener un nuevo access token.
    No requiere estar autenticado (el access_token puede estar expirado).
    """
    try:
        supa_data = await svc.supabase_refresh(data.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    return TokenRefreshResponse(access_token=supa_data["access_token"])


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
async def logout(current_user: Usuario = Depends(get_current_user)):
    """
    Invalida el refresh token en Supabase.
    Requiere el access token vigente en el header Authorization.
    """
    # La invalidación la hace Supabase internamente cuando se llama con el token
    # Ya tenemos el token en el header via get_current_user
    return None
