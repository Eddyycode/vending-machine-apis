"""
services/auth_service.py — Lógica de negocio de autenticación.
Comunica con Supabase Auth REST API y gestiona el registro en nuestra BD.
"""
import httpx
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import Usuario, Rol, Wallet
from app.schemas.user import RegisterRequest


# ─── Supabase Auth API helpers ─────────────────────────────────────────────

SUPABASE_AUTH_URL = f"{settings.supabase_url}/auth/v1"
HEADERS = {
    "apikey":       settings.supabase_anon_key,
    "Content-Type": "application/json",
}


async def supabase_signup(email: str, password: str) -> dict:
    """
    Crea usuario en Supabase Auth.
    - Si email confirmation está OFF → retorna access_token + refresh_token + user
    - Si email confirmation está ON  → retorna solo el user (sin tokens, pendiente confirmar email)
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{SUPABASE_AUTH_URL}/signup",
            headers=HEADERS,
            json={"email": email, "password": password},
        )
    data = resp.json()

    if resp.status_code not in (200, 201):
        error_msg = (
            data.get("msg")
            or data.get("error_description")
            or data.get("message")
            or f"Supabase error {resp.status_code}"
        )
        raise ValueError(error_msg)

    # Supabase puede retornar 'error' dentro de un 200 (ej. email ya registrado)
    if "error" in data and data["error"]:
        raise ValueError(data.get("error_description", data.get("error", "Registration failed")))

    # Normalizar la respuesta para nuestro código:
    # Caso A (confirmación OFF): {"access_token":..., "refresh_token":..., "user": {...}}
    # Caso B (confirmación ON):  {"id":..., "email":..., "confirmation_sent_at":...}
    if "user" not in data and "id" in data:
        # Email confirmation habilitada — el usuario debe confirmar su correo
        data = {
            "user": data,
            "access_token": "",
            "refresh_token": "",
            "email_confirmation_required": True,
        }

    return data


async def supabase_login(email: str, password: str) -> dict:
    """Login en Supabase Auth. Retorna access_token, refresh_token y user."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{SUPABASE_AUTH_URL}/token?grant_type=password",
            headers=HEADERS,
            json={"email": email, "password": password},
        )
    data = resp.json()
    if resp.status_code != 200 or "error" in data:
        raise ValueError(data.get("error_description") or "Invalid credentials")
    return data


async def supabase_refresh(refresh_token: str) -> dict:
    """Renueva el access token usando el refresh token."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{SUPABASE_AUTH_URL}/token?grant_type=refresh_token",
            headers=HEADERS,
            json={"refresh_token": refresh_token},
        )
    data = resp.json()
    if resp.status_code != 200 or "error" in data:
        raise ValueError(data.get("error_description") or "Could not refresh token")
    return data


async def supabase_logout(access_token: str) -> None:
    """Invalida el refresh token en Supabase."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(
            f"{SUPABASE_AUTH_URL}/logout",
            headers={**HEADERS, "Authorization": f"Bearer {access_token}"},
        )


async def supabase_get_user(access_token: str) -> dict:
    """Obtiene el perfil de Supabase Auth usando el access token."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{SUPABASE_AUTH_URL}/user",
            headers={**HEADERS, "Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise ValueError("Invalid or expired token")
    return resp.json()


# ─── DB helpers ─────────────────────────────────────────────────────────────

async def get_rol_by_nombre(nombre: str, db: AsyncSession) -> Rol:
    result = await db.execute(select(Rol).where(Rol.nombre == nombre))
    rol = result.scalar_one_or_none()
    if not rol:
        raise ValueError(f"Rol '{nombre}' no existe en la BD")
    return rol


async def get_usuario_by_supabase_uid(supabase_uid: str, db: AsyncSession) -> Usuario | None:
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol), selectinload(Usuario.wallet))
        .where(Usuario.supabase_uid == supabase_uid)
    )
    return result.scalar_one_or_none()


async def get_usuario_by_email(email: str, db: AsyncSession) -> Usuario | None:
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol), selectinload(Usuario.wallet))
        .where(Usuario.email == email)
    )
    return result.scalar_one_or_none()


async def create_usuario_en_db(
    supabase_uid: str,
    data: RegisterRequest,
    rol: Rol,
    db: AsyncSession,
) -> Usuario:
    """
    Crea el registro de usuario en nuestra BD (no en Supabase Auth, eso ya se hizo).
    Si el rol es 'cliente', también crea su wallet vacía.
    """
    usuario = Usuario(
        supabase_uid=supabase_uid,
        rol_id=rol.id,
        nombre=data.nombre,
        apellidos=data.apellidos,
        email=data.email,
        telefono=data.telefono,
        activo=True,
    )
    db.add(usuario)
    await db.flush()   # Obtener el ID sin commitear aún

    if rol.nombre == "cliente":
        wallet = Wallet(usuario_id=usuario.id)
        db.add(wallet)

    await db.flush()
    await db.refresh(usuario, ["rol", "wallet"])
    return usuario


async def update_ultimo_login(usuario: Usuario, db: AsyncSession) -> None:
    """Actualiza el timestamp de último login."""
    usuario.ultimo_login = datetime.now(timezone.utc)
    db.add(usuario)
    await db.flush()
