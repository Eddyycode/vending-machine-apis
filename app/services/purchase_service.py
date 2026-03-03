"""
services/purchase_service.py — Lógica de compra en máquina expendedora.

Flujo (schema real Supabase — 1 transacción = 1 producto):
  1. Validar slot activo y con stock suficiente
  2. Calcular total (con descuento si hay promoción)
  3. Descontar del wallet del cliente
  4. Reducir cantidad_actual en inventario_maquina
  5. Crear registro en transacciones
  (El trigger de Supabase auto-logea el cambio en historial_inventario)
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventarioMaquina
from app.models.transaction import Transaccion
from app.models.user import Wallet


async def procesar_compra_item(
    cliente_id: UUID,
    inventario_id: UUID,
    cantidad: int,
    db: AsyncSession,
    promocion_id: UUID | None = None,
) -> Transaccion:
    """
    Compra de 1 producto en una máquina (1 call = 1 transacción).
    Lanza ValueError con mensaje legible ante cualquier falla de negocio.
    """
    # 1. Cargar slot de inventario con su producto
    result = await db.execute(
        select(InventarioMaquina)
        .options(selectinload(InventarioMaquina.producto))
        .where(InventarioMaquina.id == inventario_id)
        .where(InventarioMaquina.activo == True)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise ValueError("Slot de inventario no encontrado o inactivo")
    if inv.cantidad_actual < cantidad:
        raise ValueError(
            f"Stock insuficiente en slot {inv.slot_numero}: "
            f"disponible {inv.cantidad_actual}, solicitado {cantidad}"
        )

    precio = Decimal(str(inv.precio_venta))
    descuento = Decimal("0.00")
    subtotal = precio * cantidad
    total = subtotal - descuento

    # 2. Obtener wallet del cliente
    w_res = await db.execute(
        select(Wallet).where(Wallet.usuario_id == cliente_id, Wallet.activa == True)
    )
    wallet = w_res.scalar_one_or_none()
    if not wallet:
        raise ValueError("El cliente no tiene wallet activa")
    if Decimal(str(wallet.balance)) < total:
        raise ValueError(
            f"Saldo insuficiente: tienes ${wallet.balance}, necesitas ${total}"
        )

    # 3. Descontar wallet
    wallet.balance = Decimal(str(wallet.balance)) - total
    db.add(wallet)

    # 4. Reducir stock
    inv.cantidad_actual -= cantidad
    db.add(inv)

    # 5. Crear transacción (el trigger de Supabase auto-loga en historial_inventario)
    tx = Transaccion(
        cliente_id=cliente_id,
        maquina_id=inv.maquina_id,
        inventario_id=inv.id,
        producto_id=inv.producto_id,
        wallet_id=wallet.id,
        promocion_id=promocion_id,
        cantidad=cantidad,
        precio_unitario=precio,
        descuento_aplicado=descuento,
        total=total,
        estado="completada",
        medio_pago="wallet",
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    return tx


async def get_historial_cliente(
    cliente_id: UUID,
    db: AsyncSession,
    limit: int = 20,
) -> tuple[list[Transaccion], int]:
    result = await db.execute(
        select(Transaccion)
        .where(Transaccion.cliente_id == cliente_id)
        .order_by(Transaccion.created_at.desc())
        .limit(limit)
    )
    items = list(result.scalars().all())
    return items, len(items)


async def get_transaccion(tx_id: UUID, db: AsyncSession) -> Transaccion | None:
    result = await db.execute(
        select(Transaccion).where(Transaccion.id == tx_id)
    )
    return result.scalar_one_or_none()
