from finanzas.periodo import limpiar_pantalla, pausar, obtener_fecha, depurar, en_periodo, VolverAlMenuException
from finanzas.margenes import seleccionar_o_crear_categoria, solicitar_con_aviso

CATEGORIAS_NO_OPERATIVAS = {"compra_mercancia"}

def movimientos_egreso(db: dict, desde=None, hasta=None, solo_operativos=False) -> list:
    resultado = []
    for m in db.get("caja", {}).get("movimientos", []):
        if m.get("tipo") != "EGRESO":
            continue
        if not en_periodo(m.get("fecha", ""), desde, hasta):
            continue
        if solo_operativos and m.get("categoria") in CATEGORIAS_NO_OPERATIVAS:
            continue
        resultado.append(m)
    return resultado

def total_egresos(db: dict, desde=None, hasta=None, solo_operativos=False) -> float:
    movs = movimientos_egreso(db, desde, hasta, solo_operativos)
    return round(sum(abs(m.get("monto", 0)) for m in movs), 2)

def egresos_por_categoria(db: dict, desde=None, hasta=None) -> dict:
    totales = {}
    for m in movimientos_egreso(db, desde, hasta):
        cat = m.get("categoria", "sin_categoria")
        totales[cat] = totales.get(cat, 0) + abs(m.get("monto", 0))
    return {cat: round(total, 2) for cat, total in totales.items()}

def registrar_gasto(gestor):
    from base import TransaccionDB
    try:
        monto = solicitar_con_aviso("Monto del gasto ($) [Ej: 45.00]: ", float)
        if monto <= 0:
            depurar("El monto debe ser mayor a cero.", "ADVER")
            pausar()
            return
            
        with TransaccionDB(gestor) as db:
            categoria_gasto = seleccionar_o_crear_categoria(db, tipo="gastos")
            if db["caja"]["saldo_actual"] < monto:
                depurar("El gasto supera el saldo actual en caja, pero se registrará igual.", "ADVER")
            
            db["caja"]["saldo_actual"] -= monto
            db["caja"]["movimientos"].append({
                "fecha": obtener_fecha(),
                "tipo": "EGRESO",
                "categoria": categoria_gasto,
                "monto": -monto
            })
            limpiar_pantalla()
            depurar(f"Gasto registrado en caja bajo la categoría [{categoria_gasto}].", "OK")
    except VolverAlMenuException:
        pass
    except Exception as e:
        depurar(f"Error al registrar el gasto: {e}", "ERROR")
    
    pausar()
