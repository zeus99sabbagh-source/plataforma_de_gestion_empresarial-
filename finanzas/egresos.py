from base import TransaccionDB, VolverAlMenuException, limpiar_pantalla, pausar, obtener_fecha, depurar
from finanzas.margenes import solicitar_con_aviso, seleccionar_o_crear_categoria

def registrar_gasto(gestor):
    try:
        concepto = solicitar_con_aviso("Concepto del gasto [Ej: Pago de electricidad]: ")
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
                "concepto": concepto,
                "monto": -monto
            })
            limpiar_pantalla()
            depurar(f"Gasto registrado en caja bajo la categoría [{categoria_gasto}].", "OK")
    except VolverAlMenuException:
        pass
    except Exception as e:
        depurar(f"Error al registrar el gasto: {e}", "ERROR")
    pausar()