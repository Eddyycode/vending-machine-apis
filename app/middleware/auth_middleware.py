"""
middleware/auth_middleware.py — Dependencies de FastAPI para auth y roles.

Uso en cualquier router:
    @router.get("/protected")
    async def endpoint(user: Usuario = Depends(get_current_user)):
        ...

    @router.get("/solo-operadores")
    async def endpoint(user: Usuario = Depends(require_role("operador", "admin"))):
        ...
"""
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.services.auth_service import supabase_get_user, get_usuario_by_supabase_uid

# Cuántas horas puede pasar un operador/admin sin re-logearse
OPERATOR_SESSION_MAX_HOURS = 24

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Dependency principal de autenticación.

    1. Extrae el JWT del header Authorization: Bearer <token>
    2. Valida el token con Supabase Auth (GET /auth/v1/user)
    3. Busca al usuario en nuestra BD
    4. Para operadores/admins: verifica que no hayan pasado más de 24h desde ultimo_login
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    access_token = credentials.credentials

    # 1. Validar token con Supabase
    try:
        supa_user = await supabase_get_user(access_token)
    except Exception:
        raise credentials_exception

    supabase_uid = supa_user.get("id")
    if not supabase_uid:
        raise credentials_exception

    # 2. Buscar en nuestra BD
    usuario = await get_usuario_by_supabase_uid(supabase_uid, db)
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # 3. Verificar sesión por rol (operadores/admins: máx 24h)
    if usuario.rol.nombre in ("operador", "admin"):
        if usuario.ultimo_login is None:
            # Nunca hizo login → forzar login
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please log in again.",
            )
        now = datetime.now(timezone.utc)
        last = usuario.ultimo_login
        # Asegurar que last sea timezone-aware
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if (now - last) > timedelta(hours=OPERATOR_SESSION_MAX_HOURS):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired after 24h. Please log in again.",
            )

    return usuario


def require_role(*roles: str):
    """
    Factory de dependencies para control de acceso por rol.

    Ejemplo:
        Depends(require_role("admin"))
        Depends(require_role("operador", "admin"))
    """
    async def _check_role(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol.nombre not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {', '.join(roles)}",
            )
        return current_user
    return _check_role
