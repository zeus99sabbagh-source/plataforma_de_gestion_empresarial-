import json
import math
import os
import tempfile
import shutil
from datetime import datetime

# Importamos utilidades y excepciones desde finanzas.periodo para unificar el contexto
from finanzas.periodo import (
    VolverAlMenuException, limpiar_pantalla, pausar, depurar, obtener_fecha,
    preparar_terminal, encabezado, menu_opciones, panel_kpis, dinero,
)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_DB = os.path.join(DIRECTORIO_ACTUAL, "empresa_db.json")

MAX_FALLOS_SEGUIDOS = 5   # Si el menú falla tantas veces seguidas, se cierra en vez de ciclar


# =====================================================================
#  >>> MI PARTE <<<  ESTRUCTURA Y NORMALIZACIÓN DE LA BASE DE DATOS
#  Un JSON válido pero incompleto, con tipos equivocados o con registros
#  viejos no debe tumbar el sistema: se completa lo que falte.
# =====================================================================
def _estructura_base():
    return {
        "inventario": {},
        "categorias": ["General", "Víveres", "Limpieza", "Bebidas"],
        "categorias_gastos": ["Operativo", "Administrativo", "Mercancía", "Servicios"],
        "clientes": {},
        "ventas": [],
        "caja": {"saldo_actual": 0.0, "movimientos": []}
    }


def _es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)


def _normalizar(data):
    """Completa claves y registros faltantes. Lanza ValueError si el JSON no es un objeto."""
    if not isinstance(data, dict):
        raise ValueError("La base de datos no es un objeto JSON.")
    for clave, defecto in _estructura_base().items():
        if not isinstance(data.get(clave), type(defecto)):
            data[clave] = defecto

    if not data["categorias"]:
        data["categorias"] = ["General", "Víveres", "Limpieza", "Bebidas"]
    if "General" not in data["categorias"]:
        data["categorias"].insert(0, "General")
    if not data["categorias_gastos"]:
        data["categorias_gastos"] = ["Operativo", "Administrativo", "Mercancía", "Servicios"]

    data["inventario"] = {c: p for c, p in data["inventario"].items() if isinstance(p, dict)}
    for p in data["inventario"].values():
        p.setdefault("nombre", "(sin nombre)")
        p.setdefault("categoria", "General")
        for campo in ("costo", "precio", "stock"):
            if not _es_numero(p.get(campo)):
                p[campo] = 0
        if "stock_min" in p and not _es_numero(p["stock_min"]):
            p["stock_min"] = 5
    data["clientes"] = {c: v for c, v in data["clientes"].items() if isinstance(v, dict)}
    for c in data["clientes"].values():
        c.setdefault("nombre", "(sin nombre)")
        c.setdefault("telefono", "N/A")
        if not _es_numero(c.get("compras")):
            c["compras"] = 0
    data["ventas"] = [v for v in data["ventas"] if isinstance(v, dict)]
    for v in data["ventas"]:
        for campo in ("total", "ganancia_neta"):
            if not _es_numero(v.get(campo)):
                v[campo] = 0

    caja = data["caja"]
    if not isinstance(caja.get("movimientos"), list):
        caja["movimientos"] = []
    caja["movimientos"] = [m for m in caja["movimientos"] if isinstance(m, dict)]
    for m in caja["movimientos"]:
        m.setdefault("tipo", "")
        m.setdefault("fecha", "")
        if not _es_numero(m.get("monto")):
            m["monto"] = 0
        if m["tipo"] == "EGRESO" and "categoria" not in m:
            m["categoria"] = "Operativo"
    if not _es_numero(caja.get("saldo_actual")):
        caja["saldo_actual"] = round(sum(m["monto"] for m in caja["movimientos"]), 2)
    return data


# --- GESTIÓN DE PERSISTENCIA Y TRANSACCIONES ---
class GestorPersistencia:
    def __init__(self, archivo_db=ARCHIVO_DB):
        self.archivo_db = archivo_db

    def cargar(self):
        if not os.path.exists(self.archivo_db):
            return _estructura_base()
        try:
            with open(self.archivo_db, "r", encoding="utf-8") as f:
                data = json.load(f)
            return _normalizar(data)
        except ValueError:      # JSON roto, bytes inválidos o estructura que no es un objeto
            apartado = self._apartar_archivo_corrupto()
            extra = f" Se conservó una copia en '{os.path.basename(apartado)}'." if apartado else ""
            depurar("Base de datos corrupta. Inicializando estructura limpia..." + extra, "ERROR")
            return _estructura_base()
        # Un error de lectura del disco (OSError) NO se atrapa aquí: si se devolviera una base
        # vacía, el siguiente guardado borraría datos buenos. El menú lo avisa y sigue.

    def _apartar_archivo_corrupto(self):
        """Renombra el archivo dañado para no perderlo cuando se guarde la base nueva."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_nombre = os.path.splitext(self.archivo_db)[0]
        destino = f"{base_nombre}_corrupta_{timestamp}.json"
        try:
            os.replace(self.archivo_db, destino)
            return destino
        except OSError:
            return None

    def guardar(self, db):
        dir_name = os.path.dirname(self.archivo_db) or "."
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8", suffix=".tmp") as tf:
                temp_name = tf.name
                json.dump(db, tf, indent=4, ensure_ascii=False, allow_nan=False)
                tf.flush()
                os.fsync(tf.fileno())
            os.replace(temp_name, self.archivo_db)
        except Exception:
            if temp_name and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)    # No dejar archivos temporales huérfanos
                except OSError:
                    pass
            raise

    def crear_backup(self):
        if not os.path.exists(self.archivo_db):
            return False, "El archivo de base de datos aún no existe."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        carpeta = os.path.dirname(self.archivo_db) or "."   # Junto a la base, que es donde se buscan al restaurar
        nombre_backup = os.path.join(carpeta, f"empresa_db_backup_{timestamp}.json")
        try:
            shutil.copy2(self.archivo_db, nombre_backup)
            return True, nombre_backup
        except Exception as e:
            return False, str(e)

    def restaurar_backup(self, archivo_backup):
        if not os.path.exists(archivo_backup):
            return False, "El archivo de respaldo seleccionado no existe."
        try:
            with open(archivo_backup, "r", encoding="utf-8") as f:
                _normalizar(json.load(f))       # Solo se restaura un respaldo que se pueda leer
        except (ValueError, OSError) as e:
            return False, f"El respaldo no es válido y no se restauró ({e})."
        try:
            shutil.copy2(archivo_backup, self.archivo_db)
            return True, "Restauración exitosa."
        except Exception as e:
            return False, str(e)

    def eliminar_archivo_db(self):
        if os.path.exists(self.archivo_db):
            try:
                os.remove(self.archivo_db)
                return True, "Archivo de base de datos eliminado correctamente."
            except Exception as e:
                return False, str(e)
        return False, "El archivo de base de datos no existe."

class TransaccionDB:
    def __init__(self, gestor):
        self.gestor = gestor
        self.db = gestor.cargar()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if issubclass(exc_type, VolverAlMenuException):
                depurar("Operación cancelada. No se guardó ningún cambio.", "INFO")
                return True
            depurar(f"Error en transacción: {exc_val}. Revirtiendo cambios...", "ADVER")
            return False
        else:
            try:
                self.gestor.guardar(self.db)
            except Exception as e:
                depurar(f"No se pudo guardar los cambios en disco ({e}). "
                        "La última operación NO quedó registrada.", "ERROR")
            return True

# --- MENÚ PRINCIPAL ---
def mostrar_menu_principal(db):
    limpiar_pantalla()
    encabezado("Menú principal")
    inventario = db.get("inventario", {})
    bajos = sum(1 for p in inventario.values() if p.get("stock", 0) <= p.get("stock_min", 5))
    saldo = db.get("caja", {}).get("saldo_actual", 0.0)
    print()
    panel_kpis("Resumen", [
        ("Saldo en caja", dinero(saldo), "verde" if saldo >= 0 else "rojo"),
        ("Productos / Clientes", f"{len(inventario)} / {len(db.get('clientes', {}))}", ""),
        ("Ventas realizadas", str(len(db.get("ventas", []))), ""),
        ("Alertas de stock", f"{bajos} producto(s)" if bajos else "Todo en orden", "rojo" if bajos else "verde"),
    ])
    print()
    menu_opciones("Opciones", [
        ("1", "Registrar Venta (POS)", "verde"),
        ("2", "Agregar / Actualizar Producto", "amarillo"),
        ("3", "Gestión de Inventario (Ver / Eliminar Productos y Categorías)", "amarillo"),
        ("4", "Registrar Cliente", "cyan"),
        ("5", "Registrar Gasto (Egreso)", "magenta"),
        ("6", "Ver Dashboard (KPIs)", "azul"),
        ("7", "Gestión de Archivo JSON (Backup / Info / Reinicio)", "gris"),
        ("8", "Salir", "rojo"),
        ("9", "Multi-Almacén, Logística y Contabilidad (SQLite)", "cyan"),
    ])


def menu(gestor=None, preparar=True):
    gestor = gestor or GestorPersistencia()
    if preparar:
        preparar_terminal()
    
    # Importaciones locales dentro de la función para evitar importaciones circulares
    from finanzas.periodo import registrar_venta, registrar_cliente
    from finanzas.margenes import agregar_producto, menu_inventario
    from finanzas.egresos import registrar_gasto
    from finanzas.dashboard import ver_dashboard, gestionar_archivo_json
    from finanzas.inventario import menu_inventario as menu_multialmacen
    
    fallos_seguidos = 0
    try:
        while True:
            try:
                db = gestor.cargar()
                mostrar_menu_principal(db)
                opcion = input("\nSeleccione una opción [Ej: 1]: ").strip()
                
                if opcion == "1":
                    registrar_venta(gestor)
                elif opcion == "2":
                    with TransaccionDB(gestor) as db_trans:
                        agregar_producto(db_trans)
                elif opcion == "3":
                    menu_inventario(gestor)
                elif opcion == "4":
                    with TransaccionDB(gestor) as db_trans:
                        registrar_cliente(db_trans)
                elif opcion == "5":
                    registrar_gasto(gestor)
                elif opcion == "6":
                    ver_dashboard(db)
                elif opcion == "7":
                    gestionar_archivo_json(gestor)
                elif opcion == "8":
                    limpiar_pantalla()
                    depurar("Cerrando sistema... ¡Hasta luego!", "INFO")
                    return
                elif opcion == "9":
                    menu_multialmacen()
                else:
                    depurar("Opción no válida seleccionada en el menú.", "ADVER")
                    pausar()
                fallos_seguidos = 0
            except VolverAlMenuException:
                depurar("Operación cancelada por el usuario. Regresando al menú...", "INFO")
                pausar()
            except EOFError:
                raise               # Ctrl+D: lo atiende el bloque de salida limpia
            except Exception as problema:
                # Red de seguridad: un error imprevisto cancela la operación, no el programa
                fallos_seguidos += 1
                depurar(f"Error inesperado ({type(problema).__name__}: {problema}). "
                        "La operación se canceló y el sistema sigue funcionando.", "ERROR")
                if fallos_seguidos >= MAX_FALLOS_SEGUIDOS:
                    depurar("Demasiados errores seguidos. Se cierra el sistema por seguridad.", "ERROR")
                    return
                pausar()
    except (KeyboardInterrupt, EOFError):
        print()   # Ctrl+C o Ctrl+D: se sale sin mostrar errores
        depurar("Cerrando sistema... ¡Hasta luego!", "INFO")

if __name__ == "__main__":
    menu()
