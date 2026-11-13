import os
from datetime import datetime

# --- CONFIGURACIÓN DE DEPURACIÓN Y CONTROL ---
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

def en_periodo(fecha: str, desde: str | None = None, hasta: str | None = None) -> bool:
    dia = fecha[:10]
    if desde and dia < desde:
        return False
    if hasta and dia > hasta:
        return False
    return True

def registrar_venta(gestor):
    from finanzas.margenes import obtener_tabla_inventario, obtener_tabla_clientes, solicitar_con_aviso
    from base import TransaccionDB  # Importación local para evitar ciclos
    try:
        with TransaccionDB(gestor) as db:
            if not db["inventario"]:
                limpiar_pantalla()
                depurar("Inventario vacío al intentar realizar una venta.", "ADVER")
                pausar()
                return
            header_text_prod = obtener_tabla_inventario(db, "🛒 Seleccione el producto a vender:")
            codigo = solicitar_con_aviso("Código del producto a vender [Ej: P001]: ", header_extra=header_text_prod).upper()
            if codigo not in db["inventario"]:
                raise ValueError("Producto no encontrado.")
            producto = db["inventario"][codigo]
            cantidad = solicitar_con_aviso(f"Cantidad de '{producto['nombre']}' (Disponible: {producto['stock']}) [Ej: 2]: ", int)
            
            if cantidad <= 0 or cantidad > producto["stock"]:
                raise ValueError("Cantidad inválida o stock insuficiente.")
            
            header_text_cli = obtener_tabla_clientes(db, "👤 Seleccione el cliente:")
            id_cliente_input = solicitar_con_aviso(
                "ID del cliente (o presione Enter para 'Consumidor Final'): ", 
                str, 
                permitir_vacio=True, 
                header_extra=header_text_cli
            )
            
            nombre_cliente = "Consumidor Final"
            if id_cliente_input in db["clientes"]:
                nombre_cliente = db["clientes"][id_cliente_input]["nombre"]
                db["clientes"][id_cliente_input]["compras"] = db["clientes"][id_cliente_input].get("compras", 0) + 1
            
            total_venta = cantidad * producto["precio"]
            costo_total = cantidad * producto.get("costo", 0)
            ganancia = total_venta - costo_total
            fecha = obtener_fecha()
            producto["stock"] -= cantidad
            
            db["ventas"].append({
                "fecha": fecha, "producto": producto["nombre"],
                "cantidad": cantidad, "total": total_venta,
                "ganancia_neta": ganancia, "cliente": nombre_cliente
            })
            db["caja"]["saldo_actual"] += total_venta
            db["caja"]["movimientos"].append({
                "fecha": fecha, "tipo": "INGRESO",
                "concepto": f"Venta {cantidad}x {producto['nombre']} ({nombre_cliente})",
                "monto": total_venta
            })
            limpiar_pantalla()
            depurar(f"Venta procesada con éxito. Total cobrado: ${total_venta:.2f}", "OK")
    except VolverAlMenuException:
        raise
    except Exception as e:
        depurar(f"Operación de venta cancelada o errónea: {e}", "ERROR")
    pausar()

def registrar_cliente(db):
    from finanzas.margenes import solicitar_con_aviso
    id_cliente = solicitar_con_aviso("Cédula / RIF / ID del cliente [Ej: V-12345678]: ")
    if id_cliente in db["clientes"]:
        limpiar_pantalla()
        depurar("El cliente ya se encuentra registrado en el sistema.", "ADVER")
        pausar()
        return
    nombre = solicitar_con_aviso("Nombre o Razón Social: ")
    telefono = solicitar_con_aviso("Teléfono de contacto: ")
    db["clientes"][id_cliente] = {"nombre": nombre, "telefono": telefono, "compras": 0}
    limpiar_pantalla()
    depurar("Cliente registrado con éxito.", "OK")
    pausar()