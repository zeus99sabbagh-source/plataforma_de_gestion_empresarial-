# Tiene formato "YYYY-MM-DD HH:MM:SS"
# Recibe el formato de llegada del producto y se compara entre el periodo establecido.
# Primer paramétro la fecha del producto a revisar.
# Parámetros dos y tres son el periodo donde es aceptable el producto.
def en_periodo(fecha: str, desde: str | None = None, hasta: str | None = None) -> bool:
    # Extrae la fecha Año/Mes/Dia.
    dia = fecha[:10]
    # Si desde tiene fecha y la fecha del producto es anterior a la fecha mínima devuelve False.
    if desde and dia < desde:
        return False
    # Si hasta tiene fecha y la fecha del producto es después de la fecha máxima devuelve False.
    if hasta and dia > hasta:
        return False
    # Devuelve verdadero porque la fecha está dentro del periodo establecido.
    return True