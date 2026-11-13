import os
from datetime import datetime
from finanzas.periodo import limpiar_pantalla, pausar, verificar_salida, depurar

def ver_dashboard(db):
    limpiar_pantalla()
    print("================ DASHBOARD GERENCIAL ================")
    total_ingresos = sum(v["total"] for v in db["ventas"])
    ganancia_bruta = sum(v["ganancia_neta"] for v in db["ventas"])
    total_egresos = sum(abs(m["monto"]) for m in db["caja"]["movimientos"] if m["tipo"] == "EGRESO")
    
    print(f"Saldo actual en Caja:        ${db['caja']['saldo_actual']:.2f}")
    print(f"Ingresos totales por venta: ${total_ingresos:.2f}")
    print(f"Ganancia real (Margen):      ${ganancia_bruta:.2f}")
    print(f"Egresos operativos:          ${total_egresos:.2f}")
    print(f"Total de ventas realizadas: {len(db['ventas'])}")
    
    bajo_stock = [p["nombre"] for p in db["inventario"].values() if p["stock"] <= p.get("stock_min", 5)]
    if bajo_stock:
        print(f"ALERTA DE REPOSICIÓN:        {', '.join(bajo_stock)}")
    print("=====================================================")
    pausar()

def gestionar_archivo_json(gestor):
    while True:
        limpiar_pantalla()
        print("=== GESTIÓN DEL ARCHIVO DE BASE DE DATOS (JSON) ===")
        print("1. Ver Estado e Info del Archivo")
        print("2. Crear Copia de Seguridad (Backup)")
        print("3. Restaurar Copia de Seguridad")
        print("4. Eliminar base de datos actual y reiniciar")
        print("5. Volver al Menú Principal")
        
        op = input("\nSeleccione una opción [Ej: 1]: ").strip()
        verificar_salida(op)
        
        if op == "1":
            limpiar_pantalla()
            print("--- ESTADO DEL ARCHIVO ---")
            if os.path.exists(gestor.archivo_db):
                tamano_bytes = os.path.getsize(gestor.archivo_db)
                modificacion = datetime.fromtimestamp(os.path.getmtime(gestor.archivo_db)).strftime("%Y-%m-%d %H:%M:%S")
                db = gestor.cargar()
                print(f"Ruta del archivo:       {os.path.abspath(gestor.archivo_db)}")
                print(f"Tamaño en disco:        {tamano_bytes} bytes ({tamano_bytes / 1024:.2f} KB)")
                print(f"Última modificación:    {modificacion}")
                print(f"Categorías productos:   {len(db.get('categorias', []))}")
                print(f"Categorías gastos:      {len(db.get('categorias_gastos', []))}")
                print(f"Productos registrados:  {len(db.get('inventario', {}))}")
                print(f"Clientes registrados:   {len(db.get('clientes', {}))}")
                print(f"Ventas totales:         {len(db.get('ventas', {}))}")
                print(f"Movimientos de caja:    {len(db.get('caja', {}).get('movimientos', []))}")
            else:
                depurar("El archivo de base de datos aún no ha sido creado.", "ADVER")
            pausar()
            
        elif op == "2":
            limpiar_pantalla()
            print("--- CREAR COPIA DE SEGURIDAD ---")
            exito, resultado = gestor.crear_backup()
            if exito:
                depurar(f"Backup creado exitosamente. Guardado como: {resultado}", "OK")
            else:
                depurar(f"Error al crear backup: {resultado}", "ERROR")
            pausar()
            
        elif op == "3":
            limpiar_pantalla()
            print("--- RESTAURAR COPIA DE SEGURIDAD ---")
            directorio_base = os.path.dirname(gestor.archivo_db)
            backups = [f for f in os.listdir(directorio_base) if f.startswith("empresa_db_backup_") and f.endswith(".json")]
            
            if not backups:
                depurar("No se encontraron archivos de respaldo en el directorio.", "ADVER")
                pausar()
                continue
                
            print("Backups disponibles:")
            for i, b in enumerate(backups, 1):
                print(f"{i}. {b}")
                
            eleccion = input("\nNúmero del backup a restaurar (o presione Enter para cancelar) [Ej: 1]: ").strip()
            verificar_salida(eleccion)
            
            if eleccion.isdigit():
                idx = int(eleccion) - 1
                if 0 <= idx < len(backups):
                    confirmacion = input(f"¿Estás seguro de reemplazar la base de datos actual con '{backups[idx]}'?: (s/n): ").strip().lower()
                    verificar_salida(confirmacion)
                    if confirmacion == 's':
                        exito, mensaje = gestor.restaurar_backup(os.path.join(directorio_base, backups[idx]))
                        depurar(mensaje, "OK" if exito else "ERROR")
                    else:
                        depurar("Restauración cancelada.", "INFO")
                else:
                    depurar("Opción de respaldo inválida.", "ADVER")
            pausar()
            
        elif op == "4":
            limpiar_pantalla()
            print("⚠️ --- ELIMINAR BASE DE DATOS Y REINICIAR ---")
            print(f"Archivo actual: {os.path.abspath(gestor.archivo_db)}")
            print("¡Atención! Esta acción eliminará permanentemente todos los registros actuales.")
            
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