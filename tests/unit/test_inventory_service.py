"""
tests/unit/test_inventory_service.py — Tests unitarios del servicio de inventario.
No requieren BD: testean la lógica pura de build_resumen y reponer.

Ejecutar: pytest tests/unit/test_inventory_service.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import uuid

from app.models.inventory import InventarioMaquina
from app.services.inventory_service import build_resumen


# ─── build_resumen ────────────────────────────────────────────────────────────

class TestBuildResumen:
    @pytest.mark.asyncio
    async def test_todos_con_stock(self):
        items = [
            MagicMock(cantidad_actual=5),
            MagicMock(cantidad_actual=3),
        ]
        resultado = await build_resumen(items)
        assert resultado["total_slots"] == 2
        assert resultado["slots_vacios"] == 0
        assert resultado["slots_con_stock"] == 2

    @pytest.mark.asyncio
    async def test_todos_vacios(self):
        items = [
            MagicMock(cantidad_actual=0),
            MagicMock(cantidad_actual=0),
        ]
        resultado = await build_resumen(items)
        assert resultado["slots_vacios"] == 2
        assert resultado["slots_con_stock"] == 0

    @pytest.mark.asyncio
    async def test_mixto(self):
        items = [
            MagicMock(cantidad_actual=0),
            MagicMock(cantidad_actual=5),
            MagicMock(cantidad_actual=0),
        ]
        resultado = await build_resumen(items)
        assert resultado["total_slots"] == 3
        assert resultado["slots_vacios"] == 2
        assert resultado["slots_con_stock"] == 1

    @pytest.mark.asyncio
    async def test_lista_vacia(self):
        resultado = await build_resumen([])
        assert resultado["total_slots"] == 0
        assert resultado["slots_vacios"] == 0
        assert resultado["slots_con_stock"] == 0
