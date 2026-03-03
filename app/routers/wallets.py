"""
routers/wallets.py — Endpoints de Wallet y Tarjetas de Débito.

GET    /wallets/me                → Balance actual
POST   /wallets/me/recargar       → Recargar créditos (simulado)
GET    /wallets/me/historial      → Historial de recargas
POST   /wallets/me/tarjetas       → Agregar tarjeta de débito
GET    /wallets/me/tarjetas       → Listar mis tarjetas
DELETE /wallets/me/tarjetas/{id}  → Eliminar tarjeta
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.middleware.auth_middleware import get_current_user, require_role
from app.services import wallet_service as svc
from app.schemas.wallet import (
    WalletDetalleResponse,
    WalletHistorialResponse,
    AgregarTarjetaRequest,
    TarjetaResponse,
    RecargarWalletRequest,
    RecargaResponse,
)
from app.schemas.user import WalletResponse

router = APIRouter()


def _solo_clientes(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Shortcut: solo clientes pueden tener wallet."""
    if current_user.rol.nombre != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes tienen wallet",
        )
    return current_user


# ─── WALLET ───────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=WalletDetalleResponse,
    summary="Ver mi wallet (balance y moneda)",
)
async def get_my_wallet(
    current_user: Usuario = Depends(_solo_clientes),
    db: AsyncSession = Depends(get_db),
):
    wallet = await svc.get_wallet(current_user.id, db)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return WalletDetalleResponse.model_validate(wallet)


@router.get(
    "/me/historial",
    response_model=WalletHistorialResponse,
    summary="Historial de recargas",
)
async def get_historial(
    limit: int = 20,
    current_user: Usuario = Depends(_solo_clientes),
    db: AsyncSession = Depends(get_db),
):
    wallet, recargas, total = await svc.get_wallet_con_historial(current_user.id, db, limit)
    return WalletHistorialResponse(
        wallet=WalletDetalleResponse.model_validate(wallet),
        recargas=[RecargaResponse.model_validate(r) for r in recargas],
        total_recargado=total,
    )


@router.post(
    "/me/recargar",
    response_model=RecargaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Recargar créditos a la wallet",
)
async def recargar_wallet(
    data: RecargarWalletRequest,
    current_user: Usuario = Depends(_solo_clientes),
    db: AsyncSession = Depends(get_db),
):
    """
    Recarga créditos en la wallet del cliente.

    **BOSQUEJO**: La transacción está simulada.
    En producción, el frontend debe tokenizar la tarjeta con Stripe.js
    y enviar el `token_procesador` en la tarjeta guardada.
    """
    try:
        recarga = await svc.procesar_recarga(current_user.id, data, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e),
        )
    return RecargaResponse.model_validate(recarga)


# ─── TARJETAS ─────────────────────────────────────────────────────────────────

@router.get(
    "/me/tarjetas",
    response_model=list[TarjetaResponse],
    summary="Listar mis tarjetas de débito",
)
async def listar_tarjetas(
    current_user: Usuario = Depends(_solo_clientes),
    db: AsyncSession = Depends(get_db),
):
    tarjetas = await svc.listar_tarjetas(current_user.id, db)
    return [TarjetaResponse.model_validate(t) for t in tarjetas]


@router.post(
    "/me/tarjetas",
    response_model=TarjetaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar tarjeta de débito",
)
async def agregar_tarjeta(
    data: AgregarTarjetaRequest,
    current_user: Usuario = Depends(_solo_clientes),
    db: AsyncSession = Depends(get_db),
):
    """
    Agrega una tarjeta de débito.

    **Seguridad**: Solo se almacena los últimos 4 dígitos y el token del procesador.
    Nunca se almacena el número completo, CVV ni fecha de expiración.
    """
    tarjeta = await svc.agregar_tarjeta(current_user.id, data, db)
    return TarjetaResponse.model_validate(tarjeta)


@router.delete(
    "/me/tarjetas/{tarjeta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar tarjeta de débito",
)
async def eliminar_tarjeta(
    tarjeta_id: UUID,
    current_user: Usuario = Depends(_solo_clientes),
    db: AsyncSession = Depends(get_db),
):
    deleted = await svc.eliminar_tarjeta(str(tarjeta_id), str(current_user.id), db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Card not found")
