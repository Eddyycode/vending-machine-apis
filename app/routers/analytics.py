"""
routers/analytics.py — Endpoints de dashboard, alertas y mermas.

GET  /analytics/dashboard        → Resumen ejecutivo (admin/operador)
GET  /analytics/alertas          → Alertas de stock activas
POST /analytics/mermas           → Registrar merma de producto
GET  /analytics/mermas           → Historial de mermas
"""
from datetime import datetime, timezone, date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Usuario
from app.models.analytics import AlertaStock, Merma
from app.models.machine import MaquinaExpendedora
from app.models.transaction import Transaccion
from app.middleware.auth_middleware import get_current_user, require_role
from app.schemas.analytics import (
    AlertaResponse, RegistrarMermaRequest, MermaResponse, DashboardResponse,
)

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Dashboard ejecutivo (admin/operador)",
)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin", "operador")),
):
    hoy_inicio = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    # Ventas de hoy
    res_ventas = await db.execute(
        select(func.coalesce(func.sum(Transaccion.total), 0))
        .where(Transaccion.created_at >= hoy_inicio)
        .where(Transaccion.estado == "completada")
    )
    total_ventas = float(res_ventas.scalar())

    # Transacciones de hoy
    res_tx = await db.execute(
        select(func.count()).select_from(Transaccion)
        .where(Transaccion.created_at >= hoy_inicio)
    )
    total_tx = res_tx.scalar()

    # Máquinas activas vs sin stock
    res_maq = await db.execute(
        select(MaquinaExpendedora.estado, func.count())
        .where(MaquinaExpendedora.estado.in_(["activa", "sin_stock", "mantenimiento", "inactiva"]))
        .group_by(MaquinaExpendedora.estado)
    )
    maq_stats = {row[0]: row[1] for row in res_maq.all()}

    # Alertas pendientes
    res_alertas = await db.execute(
        select(func.count()).select_from(AlertaStock).where(AlertaStock.resuelta == False)
    )
    alertas = res_alertas.scalar()

    # Mermas del mes
    inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    res_mermas = await db.execute(
        select(func.coalesce(func.sum(Merma.cantidad), 0)).where(Merma.created_at >= inicio_mes)
    )
    mermas = int(res_mermas.scalar())

    return DashboardResponse(
        total_ventas_hoy=total_ventas,
        total_transacciones_hoy=total_tx,
        maquinas_activas=maq_stats.get("activa", 0),
        maquinas_sin_stock=maq_stats.get("sin_stock", 0),
        alertas_pendientes=alertas,
        mermas_mes=mermas,
    )


@router.get(
    "/alertas",
    response_model=list[AlertaResponse],
    summary="Alertas de stock activas",
)
async def get_alertas(
    resuelta: bool = False,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin", "operador")),
):
    result = await db.execute(
        select(AlertaStock)
        .where(AlertaStock.resuelta == resuelta)
        .order_by(AlertaStock.created_at.desc())
    )
    alertas = result.scalars().all()
    return [AlertaResponse.model_validate(a) for a in alertas]


@router.post(
    "/mermas",
    response_model=MermaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar merma de producto",
)
async def registrar_merma(
    data: RegistrarMermaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role("admin", "operador")),
):
    merma = Merma(
        maquina_id=data.maquina_id,
        producto_id=data.producto_id,
        cantidad=data.cantidad,
        motivo=data.motivo,
        registrado_por=current_user.id,
    )
    db.add(merma)
    await db.flush()
    await db.refresh(merma)
    return MermaResponse.model_validate(merma)


@router.get(
    "/mermas",
    response_model=list[MermaResponse],
    summary="Historial de mermas",
)
async def get_mermas(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role("admin", "operador")),
):
    result = await db.execute(
        select(Merma).order_by(Merma.created_at.desc()).limit(limit)
    )
    mermas = result.scalars().all()
    return [MermaResponse.model_validate(m) for m in mermas]
