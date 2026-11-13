from finanzas.margenes import ingresos_ventas, ganancia_bruta, ganancia_real, margen_porcentaje
from finanzas.egresos import total_egresos, egresos_por_categoria

def mostrar_dashboard(db: dict, desde=None, hasta=None) -> None:
    # Imprime los KPIs del periodo en la consola.
    periodo = f"{desde or 'inicio'} a {hasta or 'hoy'}"
    print(f"\n========== DASHBOARD GERENCIAL ({periodo}) ==========")
    print(f"Ingresos por ventas:     ${ingresos_ventas(db, desde, hasta):,.2f}")
    print(f"Ganancia bruta:          ${ganancia_bruta(db, desde, hasta):,.2f}")
    print(f"Egresos operativos:      ${total_egresos(db, desde, hasta, solo_operativos=True):,.2f}")
    print(f"Ganancia real:           ${ganancia_real(db, desde, hasta):,.2f}")
    print(f"Margen de ganancia:      {margen_porcentaje(db, desde, hasta):.2f}%")

    por_cat = egresos_por_categoria(db, desde, hasta)
    if por_cat:
        print("\nEgresos por categoría:")
        for cat, monto in sorted(por_cat.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cat:<20} ${monto:,.2f}")
    print("=" * 56)