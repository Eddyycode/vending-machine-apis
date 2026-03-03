"""
services/wallet_service.py — Lógica de negocio para Wallet y Pagos.

BOSQUEJO: Las transacciones de tarjeta están SIMULADAS.
Para producción real con Stripe:
  1. Frontend tokeniza tarjeta con Stripe.js → `stripe_token`
  2. Frontend envía stripe_token + monto → POST /wallets/me/recargar
  3. Backend: stripe.Charge.create(amount=monto_centavos, source=stripe_token)
  4. Si OK → actualizar balance + registrar recarga con referencia_externa=charge_id
"""
import uuid
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Wallet
from app.models.wallet import MetodoPago, RecargaWallet
from app.schemas.wallet import AgregarTarjetaRequest, RecargarWalletRequest


# ─── WALLET ───────────────────────────────────────────────────────────────────

async def get_wallet(usuario_id, db: AsyncSession) -> Wallet | None:
    result = await db.execute(
        select(Wallet).where(Wallet.usuario_id == usuario_id)
    )
    return result.scalar_one_or_none()


async def get_wallet_con_historial(
    usuario_id, db: AsyncSession, limit: int = 20
) -> tuple[Wallet, list[RecargaWallet], Decimal]:
    """Retorna (wallet, recargas, total_recargado)."""
    wallet = await get_wallet(usuario_id, db)
    if not wallet:
        raise ValueError("Wallet not found")

    recargas_result = await db.execute(
        select(RecargaWallet)
        .where(RecargaWallet.wallet_id == wallet.id)
        .order_by(RecargaWallet.created_at.desc())
        .limit(limit)
    )
    recargas = list(recargas_result.scalars().all())

    total_result = await db.execute(
        select(func.coalesce(func.sum(RecargaWallet.monto), Decimal("0")))
        .where(
            RecargaWallet.wallet_id == wallet.id,
            RecargaWallet.estado == "completado",
        )
    )
    total = Decimal(str(total_result.scalar() or 0))

    return wallet, recargas, total


# ─── TARJETAS ─────────────────────────────────────────────────────────────────

async def listar_tarjetas(usuario_id, db: AsyncSession) -> list[MetodoPago]:
    result = await db.execute(
        select(MetodoPago)
        .where(MetodoPago.usuario_id == usuario_id, MetodoPago.activo == True)
        .order_by(MetodoPago.es_principal.desc(), MetodoPago.created_at.desc())
    )
    return list(result.scalars().all())


async def agregar_tarjeta(
    usuario_id, data: AgregarTarjetaRequest, db: AsyncSession
) -> MetodoPago:
    """
    BOSQUEJO: genera token simulado.
    Producción → data.token_procesador viene de Stripe.js / PayPal SDK.
    """
    if data.es_predeterminado:
        tarjetas = await listar_tarjetas(usuario_id, db)
        for t in tarjetas:
            t.es_principal = False
            db.add(t)

    token = data.token_procesador or f"sim_tok_{uuid.uuid4().hex[:16]}"
    tarjeta = MetodoPago(
        usuario_id=usuario_id,
        tipo=data.tipo,
        marca=data.marca.lower(),
        ultimos_4_digitos=data.ultimos_cuatro,
        token_procesador=token,
        es_principal=data.es_predeterminado,
    )
    db.add(tarjeta)
    await db.flush()
    await db.refresh(tarjeta)
    return tarjeta


async def eliminar_tarjeta(tarjeta_id, usuario_id, db: AsyncSession) -> bool:
    """Soft delete: marca tarjeta como inactiva."""
    result = await db.execute(
        select(MetodoPago).where(
            MetodoPago.id == tarjeta_id,
            MetodoPago.usuario_id == usuario_id,
            MetodoPago.activo == True,
        )
    )
    tarjeta = result.scalar_one_or_none()
    if not tarjeta:
        return False
    tarjeta.activo = False
    db.add(tarjeta)
    return True


# ─── RECARGAS ─────────────────────────────────────────────────────────────────

async def procesar_recarga(
    usuario_id, data: RecargarWalletRequest, db: AsyncSession
) -> RecargaWallet:
    """
    BOSQUEJO: simula cargo a tarjeta y acredita balance.

    Producción (Stripe):
        charge = stripe.Charge.create(
            amount=int(data.monto * 100),
            currency="mxn",
            source=metodo_pago.token_procesador,
        )
        referencia = charge.id
    """
    wallet = await get_wallet(usuario_id, db)
    if not wallet:
        raise ValueError("Wallet not found")

    # Determinar tarjeta
    metodo_pago = None
    if data.metodo_pago_id:
        res = await db.execute(
            select(MetodoPago).where(
                MetodoPago.id == data.metodo_pago_id,
                MetodoPago.usuario_id == usuario_id,
                MetodoPago.activo == True,
            )
        )
        metodo_pago = res.scalar_one_or_none()
    else:
        res = await db.execute(
            select(MetodoPago).where(
                MetodoPago.usuario_id == usuario_id,
                MetodoPago.activo == True,
                MetodoPago.es_principal == True,
            )
        )
        metodo_pago = res.scalar_one_or_none()

    # ── SIMULACIÓN (reemplazar con SDK real) ──
    referencia_simulada = f"sim_ch_{uuid.uuid4().hex[:12]}"
    cargo_exitoso = True

    if not cargo_exitoso:
        raise ValueError("Payment declined")

    # Acreditar balance
    wallet.balance = Decimal(str(wallet.balance)) + data.monto
    db.add(wallet)

    # Registrar recarga — metadata almacena info descriptiva como JSON
    meta = {
        "monto": str(data.monto),
        "moneda": "MXN",
        "descripcion": f"Recarga de ${data.monto} MXN",
    }
    if metodo_pago:
        meta["tarjeta"] = f"*{metodo_pago.ultimos_4_digitos}"
        meta["marca"] = metodo_pago.marca

    recarga = RecargaWallet(
        wallet_id=wallet.id,
        metodo_pago_id=metodo_pago.id if metodo_pago else None,
        monto=data.monto,
        estado="completado",
        referencia_externa=referencia_simulada,
        meta_info=meta,
    )
    db.add(recarga)
    await db.flush()
    await db.refresh(recarga)
    return recarga
