"""
models/__init__.py — Importa todos los modelos para registrarlos en Base.metadata.
El orden de importación respeta las dependencias de FK:
  roles → usuarios → wallets/metodos_pago
  ubicaciones → maquinas → inventario_maquina → historial_inventario
  categorias_producto → productos
  promociones → transacciones
  alertas_stock, mermas, predicciones_demanda
"""
# Tier 1: sin FKs externas
from app.models.user import Rol, Usuario, Wallet                              # noqa: F401
from app.models.ubicacion import Ubicacion                                    # noqa: F401
from app.models.product import Categoria, Producto                            # noqa: F401

# Tier 2: dependen de Tier 1
from app.models.wallet import MetodoPago, RecargaWallet                      # noqa: F401
from app.models.machine import MaquinaExpendedora                            # noqa: F401
from app.models.promotion import Promocion                                   # noqa: F401

# Tier 3: dependen de Tier 2
from app.models.inventory import InventarioMaquina, HistorialInventario      # noqa: F401
from app.models.transaction import Transaccion                               # noqa: F401
from app.models.analytics import AlertaStock, Merma, PrediccionDemanda      # noqa: F401
