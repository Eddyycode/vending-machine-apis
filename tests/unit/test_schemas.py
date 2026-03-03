"""
tests/unit/test_schemas.py — Tests unitarios de esquemas Pydantic y validaciones.

Ejecutar: pytest tests/unit/test_schemas.py -v
"""
import pytest
from pydantic import ValidationError

from app.schemas.user import RegisterRequest, LoginRequest, RefreshRequest
from app.schemas.machine import CreateMaquinaRequest, UpdateMaquinaRequest
from app.schemas.product import CreateProductoRequest, UpdateProductoRequest
from app.schemas.inventory import AddInventarioRequest, ReponerInventarioRequest
from app.schemas.transaction import ComprarRequest, ItemCompraRequest
from app.schemas.analytics import RegistrarMermaRequest
import uuid


# ─── AUTH SCHEMAS ─────────────────────────────────────────────────────────────

class TestRegisterRequest:
    def test_valid_cliente(self):
        data = RegisterRequest(
            email="cliente@test.com",
            password="secret123",
            nombre="Juan",
            rol="cliente",
        )
        assert data.email == "cliente@test.com"
        assert data.rol == "cliente"

    def test_valid_operador(self):
        data = RegisterRequest(
            email="op@test.com",
            password="secret123",
            nombre="Maria",
            rol="operador",
        )
        assert data.rol == "operador"

    def test_email_normalized_lowercase(self):
        data = RegisterRequest(
            email="USER@EXAMPLE.COM",
            password="secret123",
            nombre="Ana",
        )
        assert data.email == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="secret123", nombre="X")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="123", nombre="X")

    def test_invalid_rol(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="a@b.com", password="secret123", nombre="X", rol="superadmin")

    def test_optional_fields(self):
        data = RegisterRequest(email="a@b.com", password="secret123", nombre="X")
        assert data.apellidos is None
        assert data.telefono is None


class TestLoginRequest:
    def test_valid_login(self):
        data = LoginRequest(email="user@test.com", password="pass1234")
        assert data.email == "user@test.com"

    def test_email_trimmed(self):
        data = LoginRequest(email="  USER@TEST.COM  ", password="pass1234")
        assert data.email == "user@test.com"


class TestRefreshRequest:
    def test_valid(self):
        data = RefreshRequest(refresh_token="some-token-value")
        assert data.refresh_token == "some-token-value"

    def test_missing_token(self):
        with pytest.raises(ValidationError):
            RefreshRequest()


# ─── MACHINE SCHEMAS ──────────────────────────────────────────────────────────

class TestCreateMaquinaRequest:
    def test_valid(self):
        data = CreateMaquinaRequest(nombre="Máquina Central", capacidad_total=100)
        assert data.capacidad_total == 100
        assert data.ubicacion is None

    def test_nombre_too_short(self):
        with pytest.raises(ValidationError):
            CreateMaquinaRequest(nombre="X")

    def test_capacidad_invalida(self):
        with pytest.raises(ValidationError):
            CreateMaquinaRequest(nombre="OK", capacidad_total=0)

    def test_capacidad_maxima(self):
        with pytest.raises(ValidationError):
            CreateMaquinaRequest(nombre="OK", capacidad_total=9999)


class TestUpdateMaquinaRequest:
    def test_estatus_invalido(self):
        with pytest.raises(ValidationError):
            UpdateMaquinaRequest(estatus="desconocido")

    def test_estatus_valido(self):
        data = UpdateMaquinaRequest(estatus="mantenimiento")
        assert data.estatus == "mantenimiento"

    def test_todos_opcionales(self):
        data = UpdateMaquinaRequest()
        assert data.nombre is None
        assert data.estatus is None


# ─── PRODUCT SCHEMAS ──────────────────────────────────────────────────────────

class TestCreateProductoRequest:
    def test_valid(self):
        data = CreateProductoRequest(nombre="Coca-Cola 355ml", precio=25.0)
        assert data.precio == 25.0

    def test_precio_negativo(self):
        with pytest.raises(ValidationError):
            CreateProductoRequest(nombre="Test", precio=-5.0)

    def test_precio_cero(self):
        with pytest.raises(ValidationError):
            CreateProductoRequest(nombre="Test", precio=0)

    def test_codigo_barras_largo(self):
        with pytest.raises(ValidationError):
            CreateProductoRequest(nombre="Test", precio=10.0, codigo_barras="X" * 60)


# ─── INVENTORY SCHEMAS ────────────────────────────────────────────────────────

class TestAddInventarioRequest:
    def test_valid(self):
        pid = uuid.uuid4()
        data = AddInventarioRequest(producto_id=pid, slot="A1", cantidad_maxima=20)
        assert data.slot == "A1"
        assert data.cantidad_maxima == 20

    def test_cantidad_negativa(self):
        with pytest.raises(ValidationError):
            AddInventarioRequest(producto_id=uuid.uuid4(), cantidad_actual=-1)


class TestReponerInventarioRequest:
    def test_valid(self):
        data = ReponerInventarioRequest(cantidad=5)
        assert data.cantidad == 5

    def test_cantidad_cero(self):
        with pytest.raises(ValidationError):
            ReponerInventarioRequest(cantidad=0)


# ─── TRANSACTION SCHEMAS ──────────────────────────────────────────────────────

class TestComprarRequest:
    def test_valid(self):
        maquina_id = uuid.uuid4()
        inv_id = uuid.uuid4()
        data = ComprarRequest(
            maquina_id=maquina_id,
            items=[ItemCompraRequest(inventario_id=inv_id, cantidad=2)],
        )
        assert len(data.items) == 1

    def test_items_vacios(self):
        with pytest.raises(ValidationError):
            ComprarRequest(maquina_id=uuid.uuid4(), items=[])

    def test_cantidad_excesiva(self):
        with pytest.raises(ValidationError):
            ItemCompraRequest(inventario_id=uuid.uuid4(), cantidad=99)


# ─── ANALYTICS SCHEMAS ────────────────────────────────────────────────────────

class TestRegistrarMermaRequest:
    def test_valid(self):
        data = RegistrarMermaRequest(
            maquina_id=uuid.uuid4(),
            producto_id=uuid.uuid4(),
            cantidad=3,
            motivo="vencimiento",
        )
        assert data.motivo == "vencimiento"

    def test_motivo_invalido(self):
        with pytest.raises(ValidationError):
            RegistrarMermaRequest(
                maquina_id=uuid.uuid4(),
                producto_id=uuid.uuid4(),
                cantidad=1,
                motivo="perdida",
            )

    def test_cantidad_cero(self):
        with pytest.raises(ValidationError):
            RegistrarMermaRequest(
                maquina_id=uuid.uuid4(),
                producto_id=uuid.uuid4(),
                cantidad=0,
                motivo="dano",
            )
