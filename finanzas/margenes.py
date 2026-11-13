from finanzas.periodo import en_periodo
from finanzas.egresos import total_egresos

# Calcula los ingresos de las ventas en un periodo asignado.
def ingresos_ventas(db: dict, desde=None, hasta=None) -> float:
    return round(sum(v["total"] for v in db["ventas"] if en_periodo(v["fecha"], desde, hasta)), 2)

# Calcula la ganancia neta en un periodo asignado.
def ganancia_bruta(db: dict, desde=None, hasta=None) -> float:
    return round(sum(v["ganancia_neta"] for v in db["ventas"] if en_periodo(v["fecha"], desde, hasta)), 2)

# Calcula la diferencia de la ganancia neta menos los gastos operativos.
def ganancia_real(db: dict, desde=None, hasta=None) -> float:
    bruta = ganancia_bruta(db, desde, hasta)
    operativos = total_egresos(db, desde, hasta, solo_operativos=True)
    return round(bruta - operativos, 2)

# Establece el porcentaje de ganancia a partir de la ganancia real y los ingresos.
def margen_porcentaje(db: dict, desde=None, hasta=None) -> float:
    """Ganancia real como porcentaje de los ingresos. Devuelve 0.0 si no hay ventas."""
    ingresos = ingresos_ventas(db, desde, hasta)
    if ingresos == 0:
        return 0.0
    return round(ganancia_real(db, desde, hasta) / ingresos * 100, 2)