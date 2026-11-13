import json
import os
import tempfile
import shutil
from datetime import datetime

# --- CONFIGURACIÓN DE BASE DE DATOS Y DEPURACIÓN ---
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_DB = os.path.join(DIRECTORIO_ACTUAL, "empresa_db.json")
MODO_DEBUG = True  # Cambia a False para silenciar los mensajes de depuración en consola

def depurar(mensaje, tipo="INFO"):
    """Función centralizada para controlar y limpiar los mensajes impresos en consola."""
    if MODO_DEBUG:
        prefijos = {
            "INFO": "ℹ️ [INFO]",
            "ADVER": "⚠️ [ADVERTENCIA]",
            "ERROR": "❌ [ERROR]",
            "OK": "✅ [ÉXITO]"
        }
        print(f"{prefijos.get(tipo, '📌')} {mensaje}")

# --- EXCEPCIÓN Y UTILIDADES GLOBALES ---
class VolverAlMenuException(Exception):
    """Excepción personalizada para abortar procesos y regresar al menú."""
    pass

def verificar_salida(texto):
    if texto.strip().lower() in ["0", "salir", "menu", "volver"]:
        raise VolverAlMenuException()

def limpiar_pantalla():
    if os.name == 'nt':
        os.system('cls')
    else:
        print("\033[2J\033[3J\033[H", end="")

def pausar():
    input("\nPresiona [Enter] para continuar...")

def obtener_fecha():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- GESTIÓN DE PERSISTENCIA Y TRANSACCIONES ---
class GestorPersistencia:
    def __init__(self, archivo_db=ARCHIVO_DB):
        self.archivo_db = archivo_db

    def cargar(self):
        if not os.path.exists(self.archivo_db):
            return {
                "inventario": {},
                "categorias": ["General", "Víveres", "Limpieza", "Bebidas"],
                "categorias_gastos": ["Operativo", "Administrativo", "Mercancía", "Servicios"],
                "clientes": {},
                "ventas": [],
                "caja": {"saldo_actual": 0.0, "movimientos": []}
            }
        try:
            with open(self.archivo_db, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "categorias" not in data or not data["categorias"]:
                    data["categorias"] = ["General", "Víveres", "Limpieza", "Bebidas"]
                if "General" not in data["categorias"]:
                    data["categorias"].insert(0, "General")
                if "categorias_gastos" not in data:
                    data["categorias_gastos"] = ["Operativo", "Administrativo", "Mercancía", "Servicios"]
                for p in data.get("inventario", {}).values():
                    if "categoria" not in p:
                        p["categoria"] = "General"
                for m in data.get("caja", {}).get("movimientos", []):
                    if m.get("tipo") == "EGRESO" and "categoria" not in m:
                        m["categoria"] = "Operativo"
                return data
        except json.JSONDecodeError:
            depurar("Base de datos corrupta. Inicializando estructura limpia...", "ERROR")
            return {
                "inventario": {},
                "categorias": ["General", "Víveres", "Limpieza", "Bebidas"],
                "categorias_gastos": ["Operativo", "Administrativo", "Mercancía", "Servicios"],
                "clientes": {},
                "ventas": [],
                "caja": {"saldo_actual": 0.0, "movimientos": []}
            }

    def guardar(self, db):
        dir_name = os.path.dirname(self.archivo_db) or "."
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(db, tf, indent=4, ensure_ascii=False)
            temp_name = tf.name
        os.replace(temp_name, self.archivo_db)

    def crear_backup(self):
        if not os.path.exists(self.archivo_db):
            return False, "El archivo de base de datos aún no existe."
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = os.path.join(DIRECTORIO_ACTUAL, f"empresa_db_backup_{timestamp}.json")
        try:
            shutil.copy2(self.archivo_db, nombre_backup)
            return True, nombre_backup
        except Exception as e:
            return False, str(e)

    def restaurar_backup(self, archivo_backup):
        if not os.path.exists(archivo_backup):
            return False, "El archivo de respaldo seleccionado no existe."
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
                return True
            depurar(f"Error en transacción: {exc_val}. Revirtiendo cambios...", "ADVER")
            return False
        else:
            self.gestor.guardar(self.db)
            return True

# --- MENÚ PRINCIPAL ---
def menu():
    gestor = GestorPersistencia()
    
    # Importaciones locales dentro de la función para romper cualquier importación circular
    from finanzas.periodo import registrar_venta, registrar_cliente
    from finanzas.margenes import agregar_producto, menu_inventario
    from finanzas.egresos import registrar_gasto
    from finanzas.dashboard import ver_dashboard, gestionar_archivo_json
    
    while True:
        db = gestor.cargar()
        limpiar_pantalla()
        
        print("=== SISTEMA DE GESTIÓN EMPRESARIAL ===")
        print("1. Registrar Venta (POS)")
        print("2. Agregar / Actualizar Producto")
        print("3. Gestión de Inventario (Ver / Eliminar Productos y Categorías)")
        print("4. Registrar Cliente")
        print("5. Registrar Gasto (Egreso)")
        print("6. Ver Dashboard (KPIs)")
        print("7. Gestión de Archivo JSON (Backup / Info / Reinicio)")
        print("8. Salir")
        
        opcion = input("\nSeleccione una opción [Ej: 1]: ").strip()
        
        try:
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
                break
            else:
                depurar("Opción no válida seleccionada en el menú.", "ADVER")
                pausar()
        except VolverAlMenuException:
            depurar("Operación cancelada por el usuario. Regresando al menú...", "INFO")
            pausar()

if __name__ == "__main__":
    menu()