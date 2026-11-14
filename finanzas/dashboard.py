import os
from datetime import datetime
from finanzas.periodo import (
    limpiar_pantalla, pausar, verificar_salida, depurar,
    encabezado, menu_opciones, panel_kpis, caja, mensaje_caja, dinero, a_entero, es_si,
)

def ver_dashboard(db):
    limpiar_pantalla()
    encabezado("Dashboard gerencial")
    ventas = db.get("ventas", [])
    movimientos = db.get("caja", {}).get("movimientos", [])
    saldo = db.get("caja", {}).get("saldo_actual", 0.0)
    total_ingresos = sum(v.get("total", 0) for v in ventas)
    ganancia_bruta = sum(v.get("ganancia_neta", 0) for v in ventas)
    total_egresos = sum(abs(m.get("monto", 0)) for m in movimientos if m.get("tipo") == "EGRESO")
    
    print()
    panel_kpis("Indicadores clave", [
        ("Saldo actual en Caja", dinero(saldo), "verde" if saldo >= 0 else "rojo"),
        ("Ingresos totales por venta", dinero(total_ingresos), "cyan"),
        ("Ganancia real (Margen)", dinero(ganancia_bruta), "verde" if ganancia_bruta >= 0 else "rojo"),
        ("Egresos operativos", dinero(total_egresos), "amarillo"),
        ("Total de ventas realizadas", str(len(ventas)), ""),
    ])
    
    bajo_stock = [p.get("nombre", "?") for p in db.get("inventario", {}).values()
                  if p.get("stock", 0) <= p.get("stock_min", 5)]
    if bajo_stock:
        print()
        print(mensaje_caja("ALERTA DE REPOSICIÓN: " + ", ".join(bajo_stock), "rojo"))
    pausar()

def gestionar_archivo_json(gestor):
    while True:
        limpiar_pantalla()
        encabezado("Gestión del archivo de base de datos (JSON)")
        menu_opciones("Opciones", [
            ("1", "Ver Estado e Info del Archivo", "cyan"),
            ("2", "Crear Copia de Seguridad (Backup)", "verde"),
            ("3", "Restaurar Copia de Seguridad", "amarillo"),
            ("4", "Eliminar base de datos actual y reiniciar", "rojo"),
            ("5", "Volver al Menú Principal", "gris"),
        ])
        
        op = input("\nSeleccione una opción [Ej: 1]: ").strip()
        verificar_salida(op)
        
        if op == "1":
            limpiar_pantalla()
            encabezado("Estado del archivo")
            print()
            if os.path.exists(gestor.archivo_db):
                tamano_bytes = os.path.getsize(gestor.archivo_db)
                modificacion = datetime.fromtimestamp(os.path.getmtime(gestor.archivo_db)).strftime("%Y-%m-%d %H:%M:%S")
                db = gestor.cargar()
                caja("Ruta del archivo", [os.path.abspath(gestor.archivo_db)])
                print()
                panel_kpis("Contenido", [
                    ("Tamaño en disco", f"{tamano_bytes} bytes ({tamano_bytes / 1024:.2f} KB)", ""),
                    ("Última modificación", modificacion, ""),
                    ("Categorías productos", str(len(db.get('categorias', []))), ""),
                    ("Categorías gastos", str(len(db.get('categorias_gastos', []))), ""),
                    ("Productos registrados", str(len(db.get('inventario', {}))), ""),
                    ("Clientes registrados", str(len(db.get('clientes', {}))), ""),
                    ("Ventas totales", str(len(db.get('ventas', {}))), ""),
                    ("Movimientos de caja", str(len(db.get('caja', {}).get('movimientos', []))), ""),
                ])
            else:
                depurar("El archivo de base de datos aún no ha sido creado.", "ADVER")
            pausar()
            
        elif op == "2":
            limpiar_pantalla()
            encabezado("Crear copia de seguridad")
            exito, resultado = gestor.crear_backup()
            if exito:
                depurar(f"Backup creado exitosamente. Guardado como: {resultado}", "OK")
            else:
                depurar(f"Error al crear backup: {resultado}", "ERROR")
            pausar()
            
        elif op == "3":
            limpiar_pantalla()
            encabezado("Restaurar copia de seguridad")
            directorio_base = os.path.dirname(gestor.archivo_db) or "."
            # Más reciente primero: el nombre lleva fecha y hora, así que el orden alfabético basta
            backups = sorted((f for f in os.listdir(directorio_base)
                              if f.startswith("empresa_db_backup_") and f.endswith(".json")), reverse=True)
            
            if not backups:
                depurar("No se encontraron archivos de respaldo en el directorio.", "ADVER")
                pausar()
                continue
                
            print()
            menu_opciones("Backups disponibles (el más reciente primero)",
                          [(str(i), b, "amarillo") for i, b in enumerate(backups, 1)])
                
            eleccion = input("\nNúmero del backup a restaurar (o presione Enter para cancelar) [Ej: 1]: ").strip()
            verificar_salida(eleccion)
            
            if not eleccion:
                depurar("Restauración cancelada.", "INFO")
            else:
                numero = a_entero(eleccion)
                if numero is not None and 1 <= numero <= len(backups):
                    idx = numero - 1
                    confirmacion = input(f"¿Estás seguro de reemplazar la base de datos actual con '{backups[idx]}'?: (s/n): ").strip().lower()
                    verificar_salida(confirmacion)
                    if es_si(confirmacion):
                        exito, mensaje = gestor.restaurar_backup(os.path.join(directorio_base, backups[idx]))
                        depurar(mensaje, "OK" if exito else "ERROR")
                    else:
                        depurar("Restauración cancelada.", "INFO")
                else:
                    depurar("Opción de respaldo inválida.", "ADVER")
            pausar()
            
        elif op == "4":
            limpiar_pantalla()
            encabezado("Eliminar base de datos y reiniciar")
            print()
            print(mensaje_caja("¡Atención! Esta acción eliminará permanentemente todos los registros actuales.", "rojo"))
            print(f"\nArchivo actual: {os.path.abspath(gestor.archivo_db)}")
            
            confirmacion1 = input("\n¿Estás completamente seguro? (escribe 'ELIMINAR' para confirmar): ").strip()
            verificar_salida(confirmacion1)
            
            if confirmacion1 == "ELIMINAR":
                exito, mensaje = gestor.eliminar_archivo_db()
                if exito:
                    depurar(mensaje, "OK")
                else:
                    depurar(mensaje, "ERROR")
            else:
                depurar("Operación cancelada.", "INFO")
            pausar()
            
        elif op == "5":
            break
        else:
            depurar("Opción no válida.", "ADVER")
            pausar()
