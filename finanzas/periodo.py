from __future__ import annotations

import math
import os
import sys
import textwrap
import unicodedata
from datetime import datetime

# --- CONFIGURACIÓN DE DEPURACIÓN Y CONTROL ---
MODO_DEBUG = True  # Cambia a False para silenciar los mensajes de depuración en consola

# =====================================================================
#  >>> MI PARTE <<<  INTERFAZ DE CONSOLA
#  Todo lo visual vive aquí (colores, marcos, tablas, mensajes). El resto
#  de los módulos solo llaman a estas funciones, así el aspecto del sistema
#  se cambia en un único lugar.
# =====================================================================
USAR_COLORES = True        # Se apaga solo si la salida no es una terminal
USAR_UNICODE = True        # Se apaga solo si la terminal no puede dibujar marcos
ANCHO = 70                 # Ancho de todos los paneles y tablas
TITULO_SISTEMA = "SISTEMA DE GESTIÓN EMPRESARIAL"
MAX_TEXTO = 60             # Largo máximo de nombres, códigos, etc.
LIMITE_NUMERICO = 1_000_000_000_000   # Tope para montos y cantidades

_COLORES = {
    "verde": "\033[92m", "rojo": "\033[91m", "amarillo": "\033[93m",
    "cyan": "\033[96m", "magenta": "\033[95m", "azul": "\033[94m",
    "gris": "\033[90m", "negrita": "\033[1m",
}
_RESET = "\033[0m"


def preparar_terminal():
    """Ajusta la terminal una sola vez al arrancar (colores, tildes y marcos)."""
    global USAR_COLORES, USAR_UNICODE
    if os.name == "nt":
        os.system("")   # Activa los códigos de color ANSI en la consola de Windows
    for flujo in (sys.stdout, sys.stdin):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass        # Algunos entornos no permiten reconfigurar: se sigue igual
    try:
        "╭─╮│╰╯├┤┬┴┼═•✔✖⚠ℹ❯…".encode(sys.stdout.encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        USAR_UNICODE = False    # La terminal no sabe dibujar marcos: se usa ASCII
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        USAR_COLORES = False    # Salida redirigida o colores desactivados por el usuario


def _g():
    """Caracteres de dibujo: bonitos si la terminal puede, ASCII si no."""
    if USAR_UNICODE:
        return {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│",
                "ml": "├", "mr": "┤", "tm": "┬", "bm": "┴", "cr": "┼",
                "ok": "✔", "err": "✖", "adv": "⚠", "info": "ℹ", "dot": "•",
                "prompt": "❯ ", "mas": "…", "punto": "·"}
    return {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|",
            "ml": "+", "mr": "+", "tm": "+", "bm": "+", "cr": "+",
            "ok": "+", "err": "x", "adv": "!", "info": "i", "dot": "*",
            "prompt": "> ", "mas": "~", "punto": "."}


def marca_prompt():
    """Símbolo que acompaña a cada pregunta (sin colores: el input() no los maneja bien)."""
    return _g()["prompt"]


def pintar(texto, *estilos):
    if not USAR_COLORES or not estilos:
        return texto
    return "".join(_COLORES[e] for e in estilos) + texto + _RESET


# ---------- medidas de texto (acentos y caracteres anchos no descuadran los marcos) ----------
def ancho_visual(texto):
    total = 0
    for ch in texto:
        if unicodedata.combining(ch):
            continue
        total += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return total


def recortar(texto, maximo):
    """Acorta un texto a 'maximo' columnas y cambia lo no imprimible por '?'."""
    texto = "".join(ch if ch.isprintable() else "?" for ch in str(texto))
    if ancho_visual(texto) <= maximo:
        return texto
    salida, usado = "", 0
    for ch in texto:
        w = ancho_visual(ch)
        if usado + w > maximo - 1:
            break
        salida += ch
        usado += w
    return salida + _g()["mas"]


def ajustar(texto, ancho, alinear="izq"):
    texto = recortar(texto, ancho)
    relleno = ancho - ancho_visual(texto)
    if alinear == "der":
        return " " * relleno + texto
    if alinear == "centro":
        izq = relleno // 2
        return " " * izq + texto + " " * (relleno - izq)
    return texto + " " * relleno


# ---------- piezas de los marcos ----------
def _componer(partes, interior):
    """Une partes [(texto, estilos)] sin pasarse del ancho. Devuelve (texto pintado, ancho usado)."""
    salida, usado = [], 0
    for texto, estilos in partes:
        restante = interior - usado
        if restante <= 0:
            break
        texto = recortar(texto, restante)
        usado += ancho_visual(texto)
        salida.append(pintar(texto, *estilos) if estilos else texto)
    return "".join(salida), usado


def _linea(partes, borde="cyan"):
    interior = ANCHO - 4
    cuerpo, usado = _componer(partes, interior)
    v = pintar(_g()["v"], borde)
    return f"{v} {cuerpo}{' ' * (interior - usado)} {v}"


def _tope(titulo=None, borde="cyan"):
    g = _g()
    if not titulo:
        return pintar(g["tl"] + g["h"] * (ANCHO - 2) + g["tr"], borde)
    t = recortar(titulo, ANCHO - 6)
    k = ANCHO - 5 - ancho_visual(t)
    return (pintar(g["tl"] + g["h"] + " ", borde) + pintar(t, "negrita")
            + pintar(" " + g["h"] * k + g["tr"], borde))


def _pie(borde="cyan"):
    g = _g()
    return pintar(g["bl"] + g["h"] * (ANCHO - 2) + g["br"], borde)


# ---------- componentes que usan los demás módulos ----------
def encabezado(subtitulo=None):
    """Cabecera con el nombre del sistema y, debajo, la sección o la ayuda."""
    print()
    print(_tope())
    print(_linea([(ajustar(TITULO_SISTEMA, ANCHO - 4, "centro"), ("negrita",))]))
    if subtitulo:
        print(_linea([(ajustar(subtitulo, ANCHO - 4, "centro"), ("gris",))]))
    print(_pie())


def caja(titulo, lineas, color="cyan"):
    print(_tope(titulo, color))
    for linea in lineas:
        print(_linea([(linea, ())], color))
    print(_pie(color))


def mensaje_caja(texto, color="amarillo"):
    """Devuelve (sin imprimir) un recuadro con un aviso, para usar como encabezado."""
    g = _g()
    lineas = [_tope(None, color)]
    for i, tramo in enumerate(textwrap.wrap(texto, ANCHO - 8) or [""]):
        icono = g["adv"] + " " if i == 0 else "  "
        lineas.append(_linea([(icono, (color,)), (tramo, ())], color))
    lineas.append(_pie(color))
    return "\n".join(lineas)


def panel_kpis(titulo, filas, color="cyan"):
    """Panel de indicadores. filas = [(etiqueta, valor, color_del_valor)]."""
    g = _g()
    interior = ANCHO - 4
    print(_tope(titulo, color))
    for etiqueta, valor, estilo in filas:
        etiqueta, valor = recortar(etiqueta, interior - 6), recortar(valor, interior - 6)
        hueco = interior - ancho_visual(etiqueta) - ancho_visual(valor) - 2
        guia = g["punto"] * max(hueco, 1)
        partes = [(etiqueta, ()), (" " + guia + " ", ("gris",)),
                  (valor, (estilo, "negrita") if estilo else ())]
        print(_linea(partes, color))
    print(_pie(color))


def menu_opciones(titulo, opciones):
    """Menú enmarcado. opciones = [(clave, texto, color)]."""
    print(_tope(titulo))
    for clave, texto, color in opciones:
        print(_linea([(f"{clave:>2}", (color, "negrita")), ("  ", ()), (texto, ())]))
    print(_pie())


def tabla(titulo, columnas, filas):
    """
    Devuelve una tabla como texto. columnas = [(encabezado, ancho, 'izq'|'der'|'centro')].
    Cada celda es un texto o una tupla (texto, color).
    """
    g, borde = _g(), "cyan"
    v = pintar(g["v"], borde)

    def separador(izq, medio, der):
        return pintar(g[izq] + g[medio].join(g["h"] * (a + 2) for _, a, _ in columnas) + g[der], borde)

    def fila(celdas):
        partes = []
        for (_, ancho, alin), celda in zip(columnas, celdas):
            texto, estilo = celda if isinstance(celda, tuple) else (celda, "")
            ajustado = ajustar(str(texto), ancho, alin)
            partes.append(" " + (pintar(ajustado, estilo) if estilo else ajustado) + " ")
        return v + v.join(partes) + v

    lineas = []
    if titulo:
        lineas.append(" " + pintar(titulo, "negrita"))
    lineas.append(separador("tl", "tm", "tr"))
    lineas.append(fila([(nombre, "negrita") for nombre, _, _ in columnas]))
    lineas.append(separador("ml", "cr", "mr"))
    for celdas in filas:
        lineas.append(fila(celdas))
    lineas.append(separador("bl", "bm", "br"))
    return "\n".join(lineas)


def dinero(valor):
    try:
        return ("-" if valor < 0 else "") + f"${abs(valor):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def depurar(mensaje, tipo="INFO"):
    """Función centralizada para controlar y limpiar los mensajes impresos en consola."""
    if MODO_DEBUG:
        g = _g()
        estilos = {
            "INFO": (g["info"], "INFO", "cyan"),
            "ADVER": (g["adv"], "ADVERTENCIA", "amarillo"),
            "ERROR": (g["err"], "ERROR", "rojo"),
            "OK": (g["ok"], "ÉXITO", "verde"),
        }
        icono, etiqueta, color = estilos.get(tipo, (g["dot"], tipo, "gris"))
        limpio = "".join(ch if ch.isprintable() else "?" for ch in str(mensaje))
        print(f"{pintar(f' {icono} {etiqueta} ', color, 'negrita')} {limpio}")


# ---------- validaciones de entrada ----------
def a_entero(texto):
    """Convierte a entero solo si son dígitos 0-9 (rechaza '²', '１', '1_0' y números gigantes)."""
    t = texto.strip()
    if not (t.isascii() and t.isdigit()):
        return None
    try:
        return int(t)
    except ValueError:      # Más de 4300 dígitos
        return None


def es_si(texto):
    return texto.strip().lower() in ("s", "si", "sí")


def validar_texto(texto, maximo=MAX_TEXTO):
    """Devuelve un mensaje de error si el texto no es aceptable, o None si está bien."""
    if not texto.isprintable():
        return "No se permiten caracteres de control ni saltos de línea."
    if len(texto) > maximo:
        return f"El texto es muy largo (máximo {maximo} caracteres, escribió {len(texto)})."
    return None


class VolverAlMenuException(Exception):
    """Excepción personalizada para abortar procesos y regresar al menú."""
    pass


def verificar_salida(texto):
    if texto.strip().lower() in ["0", "salir", "menu", "volver"]:
        raise VolverAlMenuException()


def limpiar_pantalla():
    if not sys.stdout.isatty():
        return      # Sin terminal (archivo, pruebas) no se mandan códigos de borrado
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
    if (desde or hasta) and not dia:
        return False        # Sin fecha no se puede saber si cae dentro del período
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
            header_text_prod = obtener_tabla_inventario(db, "Seleccione el producto a vender:")
            codigo = solicitar_con_aviso("Código del producto a vender [Ej: P001]: ", header_extra=header_text_prod).upper()
            if codigo not in db["inventario"]:
                raise ValueError("Producto no encontrado.")
            producto = db["inventario"][codigo]
            cantidad = solicitar_con_aviso(f"Cantidad de '{producto['nombre']}' (Disponible: {producto['stock']}) [Ej: 2]: ", int)
            
            if cantidad <= 0 or cantidad > producto["stock"]:
                raise ValueError("Cantidad inválida o stock insuficiente.")
            
            header_text_cli = obtener_tabla_clientes(db, "Seleccione el cliente:")
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
            print()
            panel_kpis("Recibo de venta", [
                ("Producto", producto["nombre"], ""),
                ("Cantidad", str(cantidad), ""),
                ("Cliente", nombre_cliente, ""),
                ("Total cobrado", dinero(total_venta), "verde"),
            ], "verde")
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
