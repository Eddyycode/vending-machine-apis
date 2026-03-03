"""
scripts/seed_db.py — Puebla la BD con datos de prueba realistas.

Inserta (idempotente — no duplica si ya existen):
  ✅ 3 Roles: admin, operador, cliente
  ✅ 5 Categorías de productos
  ✅ 12 Productos con precios reales
  ✅ 3 Ubicaciones en CDMX / GDL / MTY
  ✅ 3 Máquinas expendedoras (una por ciudad)
  ✅ Inventario para cada máquina (slots llenos)

Uso:
  cd vending-backend
  python scripts/seed_db.py
"""
import asyncio
import sys
import os
import uuid

# Asegurar que el path del proyecto esté en PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Importar modelos en orden de FK
import app.models  # noqa — registra todos los modelos
from app.models.user import Rol, Usuario, Wallet
from app.models.ubicacion import Ubicacion
from app.models.product import Categoria, Producto
from app.models.machine import MaquinaExpendedora
from app.models.inventory import InventarioMaquina
from app.database import AsyncSessionLocal


# ─── DATOS DE PRUEBA ──────────────────────────────────────────────────────────

ROLES = [
    {"nombre": "admin",    "descripcion": "Administrador del sistema con acceso total"},
    {"nombre": "operador", "descripcion": "Dueño de máquinas expendedoras"},
    {"nombre": "cliente",  "descripcion": "Usuario final que compra en las máquinas"},
]

CATEGORIAS = [
    {"nombre": "Bebidas",    "descripcion": "Refrescos, aguas, jugos, energéticas"},
    {"nombre": "Snacks",     "descripcion": "Papas, galletas, cacahuates, barras"},
    {"nombre": "Saludable",  "descripcion": "Frutas, barras de proteína, frutos secos"},
    {"nombre": "Lácteos",    "descripcion": "Leche, yogur, queso"},
    {"nombre": "Congelados", "descripcion": "Paletas, helados"},
]

PRODUCTOS = [
    # Bebidas
    {"nombre": "Coca-Cola 355ml",        "marca": "Coca-Cola",  "precio_base": 22.00, "categoria": "Bebidas",   "codigo_barras": "7501055300433"},
    {"nombre": "Agua Bonafont 600ml",    "marca": "Bonafont",   "precio_base": 14.00, "categoria": "Bebidas",   "codigo_barras": "7501031300149"},
    {"nombre": "Monster Energy Verde",   "marca": "Monster",    "precio_base": 38.00, "categoria": "Bebidas",   "codigo_barras": "7501059229041"},
    {"nombre": "Jugo Del Valle Mango",   "marca": "Del Valle",  "precio_base": 18.00, "categoria": "Bebidas",   "codigo_barras": "7501055301157"},
    # Snacks
    {"nombre": "Sabritas Origi. 45g",    "marca": "Sabritas",   "precio_base": 18.00, "categoria": "Snacks",    "codigo_barras": "7501011104037"},
    {"nombre": "Ruffles 45g",            "marca": "Sabritas",   "precio_base": 18.00, "categoria": "Snacks",    "codigo_barras": "7501011100176"},
    {"nombre": "Galletas Marinela Gansito","marca": "Marinela", "precio_base": 22.00, "categoria": "Snacks",    "codigo_barras": "7501012700026"},
    {"nombre": "Chicles Trident Menta",  "marca": "Trident",    "precio_base": 14.00, "categoria": "Snacks",    "codigo_barras": "7622300441951"},
    # Saludable
    {"nombre": "Barra PowerBar Choc.",   "marca": "PowerBar",   "precio_base": 35.00, "categoria": "Saludable", "codigo_barras": "4029679002706"},
    {"nombre": "Nueces Mix 60g",         "marca": "Sonora",     "precio_base": 28.00, "categoria": "Saludable", "codigo_barras": "7506006500015"},
    # Lácteos
    {"nombre": "Yogurt Yoplait Fresa",   "marca": "Yoplait",    "precio_base": 20.00, "categoria": "Lácteos",   "codigo_barras": "7501000635184"},
    {"nombre": "Leche Lala 250ml",       "marca": "Lala",       "precio_base": 16.00, "categoria": "Lácteos",   "codigo_barras": "7501025400018"},
]

UBICACIONES = [
    {
        "nombre":        "Torre BBVA - Planta Baja",
        "direccion":     "Paseo de la Reforma 510, Juárez",
        "ciudad":        "Ciudad de México",
        "estado":        "Ciudad de México",
        "codigo_postal": "06600",
        "latitud":       19.4284073,
        "longitud":      -99.1800462,
    },
    {
        "nombre":        "Plaza Galerías GDL - PB",
        "direccion":     "Av. Vallarta 3959, Prados Providencia",
        "ciudad":        "Guadalajara",
        "estado":        "Jalisco",
        "codigo_postal": "44670",
        "latitud":       20.6719138,
        "longitud":      -103.4054671,
    },
    {
        "nombre":        "TEC de Monterrey - CEDE",
        "direccion":     "Av. Eugenio Garza Sada 2501 Sur",
        "ciudad":        "Monterrey",
        "estado":        "Nuevo León",
        "codigo_postal": "64849",
        "latitud":       25.6513985,
        "longitud":      -100.2895658,
    },
]

MAQUINAS = [
    {"nombre": "VM-001 Torre BBVA",       "codigo_serial": "SN-VM-001-CDMX", "modelo": "Crane BevMax 4", "capacidad_total": 60},
    {"nombre": "VM-002 Galerías GDL",     "codigo_serial": "SN-VM-002-GDL",  "modelo": "Crane BevMax 4", "capacidad_total": 60},
    {"nombre": "VM-003 TEC Monterrey",    "codigo_serial": "SN-VM-003-MTY",  "modelo": "AMS 39-WIDE",    "capacidad_total": 40},
]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

async def get_or_none(db: AsyncSession, model, **filters):
    conditions = [getattr(model, k) == v for k, v in filters.items()]
    result = await db.execute(select(model).where(*conditions))
    return result.scalar_one_or_none()


async def seed_roles(db: AsyncSession) -> dict[str, Rol]:
    roles = {}
    for r in ROLES:
        existing = await get_or_none(db, Rol, nombre=r["nombre"])
        if not existing:
            existing = Rol(**r)
            db.add(existing)
            await db.flush()
            print(f"  ✅ Rol creado: {r['nombre']}")
        else:
            print(f"  ⏭️  Rol ya existe: {r['nombre']}")
        roles[r["nombre"]] = existing
    return roles


async def seed_categorias(db: AsyncSession) -> dict[str, Categoria]:
    cats = {}
    for c in CATEGORIAS:
        existing = await get_or_none(db, Categoria, nombre=c["nombre"])
        if not existing:
            existing = Categoria(**c)
            db.add(existing)
            await db.flush()
            print(f"  ✅ Categoría creada: {c['nombre']}")
        else:
            print(f"  ⏭️  Categoría ya existe: {c['nombre']}")
        cats[c["nombre"]] = existing
    return cats


async def seed_productos(db: AsyncSession, cats: dict[str, Categoria]) -> dict[str, Producto]:
    prods = {}
    for p in PRODUCTOS:
        existing = await get_or_none(db, Producto, codigo_barras=p["codigo_barras"])
        if not existing:
            cat = cats[p["categoria"]]
            existing = Producto(
                categoria_id=cat.id,
                nombre=p["nombre"],
                marca=p["marca"],
                precio_base=p["precio_base"],
                codigo_barras=p["codigo_barras"],
            )
            db.add(existing)
            await db.flush()
            print(f"  ✅ Producto creado: {p['nombre']}")
        else:
            print(f"  ⏭️  Producto ya existe: {p['nombre']}")
        prods[p["nombre"]] = existing
    return prods


async def seed_ubicaciones(db: AsyncSession) -> list[Ubicacion]:
    locs = []
    for u in UBICACIONES:
        existing = await get_or_none(db, Ubicacion, nombre=u["nombre"])
        if not existing:
            existing = Ubicacion(**u)
            db.add(existing)
            await db.flush()
            print(f"  ✅ Ubicación creada: {u['nombre']}")
        else:
            print(f"  ⏭️  Ubicación ya existe: {u['nombre']}")
        locs.append(existing)
    return locs


async def seed_maquinas(
    db: AsyncSession,
    operador: Usuario,
    ubicaciones: list[Ubicacion],
    productos: dict[str, Producto],
) -> list[MaquinaExpendedora]:
    maquinas = []
    for idx, m in enumerate(MAQUINAS):
        existing = await get_or_none(db, MaquinaExpendedora, codigo_serial=m["codigo_serial"])
        if not existing:
            existing = MaquinaExpendedora(
                operador_id=operador.id,
                ubicacion_id=ubicaciones[idx].id,
                **m,
            )
            db.add(existing)
            await db.flush()
            print(f"  ✅ Máquina creada: {m['nombre']}")
        else:
            print(f"  ⏭️  Máquina ya existe: {m['nombre']}")
        maquinas.append(existing)

    # Agregar inventario a cada máquina si está vacío
    prods_list = list(productos.values())
    for maq in maquinas:
        # Verificar si ya tiene inventario
        result = await db.execute(
            select(InventarioMaquina).where(InventarioMaquina.maquina_id == maq.id).limit(1)
        )
        if result.scalar_one_or_none():
            print(f"  ⏭️  Inventario ya existe para: {maq.nombre}")
            continue

        # Agregar los primeros 8 productos (o los disponibles) en slots 1-N
        num_slots = min(8, len(prods_list))
        for slot_num in range(1, num_slots + 1):
            prod = prods_list[slot_num - 1]
            item = InventarioMaquina(
                maquina_id=maq.id,
                producto_id=prod.id,
                slot_numero=slot_num,
                cantidad_actual=8,
                cantidad_maxima=10,
                precio_venta=prod.precio_base,
                costo_unitario=round(float(prod.precio_base) * 0.6, 2),
            )
            db.add(item)
        await db.flush()
        print(f"  ✅ Inventario creado para: {maq.nombre} ({num_slots} slots)")

    return maquinas


async def get_primer_operador(db: AsyncSession) -> Usuario | None:
    """Busca el primer usuario con rol operador o admin para asignar las máquinas."""
    result = await db.execute(
        select(Usuario)
        .join(Rol, Usuario.rol_id == Rol.id)
        .where(Rol.nombre.in_(["operador", "admin"]))
        .limit(1)
    )
    return result.scalar_one_or_none()


# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    print("🌱 Iniciando seed de la base de datos...\n")

    async with AsyncSessionLocal() as db:
        try:
            print("📋 Seeding ROLES...")
            roles = await seed_roles(db)

            print("\n🗂️  Seeding CATEGORÍAS...")
            cats = await seed_categorias(db)

            print("\n📦 Seeding PRODUCTOS...")
            prods = await seed_productos(db, cats)

            print("\n📍 Seeding UBICACIONES...")
            ubiaciones = await seed_ubicaciones(db)

            print("\n🤖 Seeding MÁQUINAS...")
            operador = await get_primer_operador(db)
            if not operador:
                print("  ⚠️  No hay operador/admin en la BD — máquinas omitidas.")
                print("     Primero registra un operador en POST /auth/register con rol='operador'")
            else:
                print(f"  👤 Usando operador: {operador.nombre} ({operador.email})")
                await seed_maquinas(db, operador, ubiaciones, prods)

            await db.commit()
            print("\n✅ Seed completado exitosamente!")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
