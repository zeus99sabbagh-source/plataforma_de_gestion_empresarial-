from finanzas.periodo import en_periodo

# Variable para limitar aquellas mercancias que no estas siendo operadas por la empresa.
CATEGORIAS_NO_OPERATIVAS = {"compra_mercancia"}

# Obtiene todos los movimientos de egreso en un periodo asignado.
def movimientos_egreso(db: dict, desde=None, hasta=None, solo_operativos=False) -> list:
    """Devuelve los movimientos de tipo EGRESO del periodo."""
    resultado = []
    for m in db["caja"]["movimientos"]:
        if m["tipo"] != "EGRESO":
            continue
        if not en_periodo(m["fecha"], desde, hasta):
            continue
        if solo_operativos and m.get("categoria") in CATEGORIAS_NO_OPERATIVAS:
            continue
        resultado.append(m)
    return resultado

# Calcula la suma de los egresos en un periodo asignado.
def total_egresos(db: dict, desde=None, hasta=None, solo_operativos=False) -> float:
    """Suma los egresos del periodo. Devuelve un número positivo."""
    movs = movimientos_egreso(db, desde, hasta, solo_operativos)
    return round(sum(abs(m["monto"]) for m in movs), 2)

# Calcula el total de egresos por categoria.
def egresos_por_categoria(db: dict, desde=None, hasta=None) -> dict:
    """Devuelve {categoria: total} de los egresos del periodo."""
    totales = {}
    for m in movimientos_egreso(db, desde, hasta):
        cat = m.get("categoria", "sin_categoria")
        totales[cat] = totales.get(cat, 0) + abs(m["monto"])
    return {cat: round(total, 2) for cat, total in totales.items()}