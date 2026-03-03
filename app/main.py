"""
main.py — Punto de entrada de la aplicación FastAPI.
Registra todos los routers, configura CORS y eventos de startup.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_db_connection
from app.routers import health, auth, users, wallets, machines, inventory, products, transactions, promotions, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de startup y shutdown de la app."""
    print(f"🚀 Vending API v{settings.app_version} starting [{settings.app_env}]")
    yield
    print("🛑 Vending API shutting down")


app = FastAPI(
    title="Vending Machine E-Commerce API",
    description="""
## Smart Vending Machine API

Backend para el sistema de e-commerce de máquinas expendedoras inteligentes.

### Módulos disponibles:
- **Auth** — Registro y autenticación via Supabase
- **Users** — Gestión de perfiles
- **Wallets** — Carteras virtuales y recargas
- **Machines** — Registro y gestión de máquinas (operadores)
- **Inventory** — Stock por máquina en tiempo real
- **Products** — Catálogo de productos
- **Transactions** — Historial de compras
- **Promotions** — Descuentos y campañas
- **Analytics** — Dashboard, alertas y reportes de mermas
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(wallets.router, prefix="/wallets", tags=["Wallet"])
app.include_router(machines.router, prefix="/machines", tags=["Machines"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(promotions.router, prefix="/promotions", tags=["Promotions"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
