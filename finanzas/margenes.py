from finanzas.periodo import limpiar_pantalla, pausar, verificar_salida, VolverAlMenuException, depurar

def obtener_tabla_inventario(db, titulo="📦 Productos disponibles en inventario:"):
    inventario = db.get("inventario", {})
    if not inventario:
        return "⚠️ El inventario está actualmente vacío."
    lineas = [
        titulo,
        "-" * 65,
        f"{'COD':<6} {'NOMBRE':<22} {'CATEGORÍA':<12} {'STOCK':<6} {'PRECIO':<8}",
        "-" * 65
    ]
    for cod, p in inventario.items():
        nombre = p['nombre'][:20]
        cat = p.get('categoria', 'General')[:10]
        stock = p['stock']
        precio = p['precio']
        lineas.append(f" {cod:<5} {nombre:<22} {cat:<12} {stock:<6} ${precio:<7.2f}")
    lineas.append("-" * 65)
    return "\n".join(lineas)

def obtener_tabla_clientes(db, titulo="📋 Clientes registrados:"):
    clientes = db.get("clientes", {})
    if not clientes:
        return "⚠️ No hay clientes registrados (se asignará 'Consumidor Final' si deja en blanco)."
    lineas = [
        titulo,
        "-" * 65,
        f"{'ID / RIF':<15} {'NOMBRE':<22} {'TELÉFONO':<15} {'COMPRAS':<8}",
        "-" * 65
    ]
    for id_c, c in clientes.items():
        nombre = c['nombre'][:20]
        tel = c.get('telefono', 'N/A')[:14]
        compras = c.get('compras', 0)
        lineas.append(f" {id_c:<14} {nombre:<22} {tel:<15} {compras:<8}")
    lineas.append("-" * 65)
    return "\n".join(lineas)

def solicitar_con_aviso(mensaje, validador_tipo=str, permitir_vacio=False, header_extra=None):
    while True:
        limpiar_pantalla()
        print("=== SISTEMA DE GESTIÓN EMPRESARIAL ===")
        print("(Escriba '0' o 'salir' en cualquier momento para volver al menú)\n")
        if header_extra:
            print(header_extra)
            print()
        entrada = input(mensaje).strip()
        verificar_salida(entrada)
        if not permitir_vacio and not entrada:
            depurar("Este campo no puede estar vacío.", "ADVER")
            input("Presiona [Enter] para intentar de nuevo...")
            continue
        if permitir_vacio and not entrada:
            return ""
        try:
            if validador_tipo == int:
                return int(entrada)
            elif validador_tipo == float:
                return float(entrada)
            else:
                return str(entrada)
        except ValueError:
            tipo_nombre = "un número entero válido" if validador_tipo == int else "un número válido (ej. 15.50)"
            depurar(f"Por favor, ingrese {tipo_nombre}.", "ADVER")
            input("Presiona [Enter] para intentar de nuevo...")

def seleccionar_o_crear_categoria(db, tipo="productos"):
    while True:
        limpiar_pantalla()
        print(f"=== SELECCIÓN DE CATEGORÍA DE {'PRODUCTOS' if tipo=='productos' else 'GASTOS'} ===")
        print("(Escriba '0' o 'salir' para volver al menú)\n")
        key = "categorias" if tipo == "productos" else "categorias_gastos"
        default_vals = ["General", "Víveres", "Limpieza", "Bebidas"] if tipo == "productos" else ["Operativo", "Administrativo", "Mercancía", "Servicios"]
        categorias = db.get(key, default_vals)
        for i, cat in enumerate(categorias, 1):
            print(f"{i}. {cat}")
        print(f"{len(categorias) + 1}. [Crear una nueva categoría]")
        print("0. Volver al Menú Principal")
        
        opcion_input = input("\nSeleccione una opción o escriba el nombre de una nueva categoría: ").strip()
        verificar_salida(opcion_input)
        if opcion_input == "0":
            raise VolverAlMenuException()
        if opcion_input.isdigit():
            idx = int(opcion_input) - 1
            if 0 <= idx < len(categorias):
                return categorias[idx]
            elif idx == len(categorias):
                while True:
                    nueva_cat = solicitar_con_aviso("Nombre de la nueva categoría (no puede estar vacío): ").strip().title()
                    if nueva_cat:
                        break
                    depurar("El nombre de la categoría no puede estar vacío.", "ADVER")
                    input("Presiona [Enter] para intentar de nuevo...")
                if nueva_cat not in categorias:
                    categorias.append(nueva_cat)
                    db[key] = categorias
                return nueva_cat
        else:
            nueva_cat = opcion_input.title()
            if not nueva_cat:
                continue
            if nueva_cat not in categorias:
                categorias.append(nueva_cat)
                db[key] = categorias
            return nueva_cat

def agregar_producto(db):
    header_text = obtener_tabla_inventario(db, "📦 Inventario actual (para referencia de códigos):")
    codigo = solicitar_con_aviso("Código del producto [Ej: P001]: ", header_extra=header_text).upper()
    if codigo in db["inventario"]:
        limpiar_pantalla()
        print("\n--- ACTUALIZAR STOCK ---")
        cant = solicitar_con_aviso(f"Producto existente ({db['inventario'][codigo]['nombre']}). Cantidad a sumar [Ej: 5]: ", int)
        if cant > 0:
            db["inventario"][codigo]["stock"] += cant
            depurar("Stock actualizado correctamente.", "OK")
        else:
            depurar("Cantidad inválida.", "ADVER")
        pausar()
        return
    nombre = solicitar_con_aviso("Nombre del producto [Ej: Café Molido 500g]: ")
    categoria = seleccionar_o_crear_categoria(db, tipo="productos")
    costo = solicitar_con_aviso("Costo unitario de compra ($) [Ej: 3.50]: ", float)
    precio = solicitar_con_aviso("Precio unitario de venta ($) [Ej: 5.00]: ", float)
    stock = solicitar_con_aviso("Stock inicial [Ej: 20]: ", int)
    stock_min = solicitar_con_aviso("Stock mínimo para alerta [Ej: 5]: ", int)
    db["inventario"][codigo] = {
        "nombre": nombre, "categoria": categoria,
        "costo": costo, "precio": precio,
        "stock": stock, "stock_min": stock_min
    }
    limpiar_pantalla()
    depurar(f"Producto '{nombre}' registrado con éxito en la categoría [{categoria}].", "OK")
    pausar()

def eliminar_producto(db):
    if not db["inventario"]:
        limpiar_pantalla()
        depurar("No hay productos registrados en el inventario.", "ADVER")
        pausar()
        return
    header_text = obtener_tabla_inventario(db, "🗑️ Seleccione el producto a eliminar:")
    codigo = solicitar_con_aviso("Ingrese el código exacto del producto a eliminar: ", header_extra=header_text).upper()
    if codigo not in db["inventario"]:
        limpiar_pantalla()
        depurar(f"El producto con código '{codigo}' no existe en el inventario.", "ERROR")
        pausar()
        return
    prod = db["inventario"][codigo]
    limpiar_pantalla()
    print("=== ELIMINAR PRODUCTO ===")
    print(f"\nProducto seleccionado: {prod['nombre']} (Código: {codigo})")
    confirmacion = input("\n¿Estás seguro de eliminar este producto permanentemente? (s/n): ").strip().lower()
    verificar_salida(confirmacion)
    if confirmacion == 's':
        del db["inventario"][codigo]
        limpiar_pantalla()
        depurar(f"Producto '{prod['nombre']}' eliminado con éxito.", "OK")
    else:
        limpiar_pantalla()
        depurar("Operación de eliminación cancelada.", "INFO")
    pausar()

def eliminar_categoria(db):
    limpiar_pantalla()
    print("=== ELIMINAR CATEGORÍA DE PRODUCTOS ===")
    categorias = db.get("categorias", ["General"])
    if len(categorias) <= 1:
        depurar("No es posible eliminar todas las categorías. Debe existir al menos una ('General').", "ADVER")
        pausar()
        return
    print("Categorías disponibles:")
    for i, cat in enumerate(categorias, 1):
        print(f"{i}. {cat}")
    opcion = input("\nSeleccione el número de la categoría que desea eliminar: ").strip()
    verificar_salida(opcion)
    if not opcion.isdigit():
        depurar("Operación cancelada.", "INFO")
        pausar()
        return
    idx = int(opcion) - 1
    if not (0 <= idx < len(categorias)):
        depurar("Opción inválida.", "ADVER")
        pausar()
        return
    cat_a_eliminar = categorias[idx]
    if cat_a_eliminar.lower() == "general":
        depurar("La categoría 'General' no se puede eliminar.", "ADVER")
        pausar()
        return
    confirmacion = input(f"\n¿Estás seguro de eliminar la categoría '{cat_a_eliminar}'? (s/n): ").strip().lower()
    verificar_salida(confirmacion)
    if confirmacion == 's':
        categorias.pop(idx)
        db["categorias"] = categorias
        for p in db.get("inventario", {}).values():
            if p.get("categoria") == cat_a_eliminar:
                p["categoria"] = "General"
        limpiar_pantalla()
        depurar(f"Categoría '{cat_a_eliminar}' eliminada y productos reasignados a 'General'.", "OK")
    pausar()

def agregar_nueva_categoria(db):
    limpiar_pantalla()
    print("=== AGREGAR NUEVA CATEGORÍA DE PRODUCTOS ===")
    nueva_cat = solicitar_con_aviso("Nombre de la nueva categoría: ").strip().title()
    if not nueva_cat:
        return
    categorias = db.get("categorias", ["General"])
    if nueva_cat in categorias:
        depurar(f"La categoría '{nueva_cat}' ya existe.", "ADVER")
    else:
        categorias.append(nueva_cat)
        db["categorias"] = categorias
        depurar(f"Categoría '{nueva_cat}' agregada exitosamente.", "OK")
    pausar()

def ver_productos_por_categoria(db):
    limpiar_pantalla()
    print("=== INVENTARIO CLASIFICADO POR CATEGORÍAS ===")
    categorias = db.get("categorias", ["General"])
    inventario = db.get("inventario", {})
    if not inventario:
        print("El inventario está vacío.")
    else:
        for cat in categorias:
            print(f"\n📁 Categoría: {cat.upper()}")
            prods = [p for p in inventario.values() if p.get("categoria", "General") == cat]
            if not prods:
                print("   (Sin productos)")
            else:
                for cod, p in inventario.items():
                    if p.get("categoria", "General") == cat:
                        alerta = " [¡STOCK BAJO!]" if p["stock"] <= p.get("stock_min", 5) else ""
                        print(f"   - [{cod}] {p['nombre']} | Stock: {p['stock']} | Costo: ${p['costo']:.2f} | Venta: ${p['precio']:.2f}{alerta}")
    pausar()

def menu_inventario(gestor):
    from base import TransaccionDB
    while True:
        db = gestor.cargar()
        limpiar_pantalla()
        print("=== GESTIÓN DE INVENTARIO ===")
        print("1. Ver Inventario por Categoría")
        print("2. Agregar Nueva Categoría de Productos")
        print("3. Eliminar Producto")
        print("4. Eliminar Categoría de Productos")
        print("5. Volver al Menú Principal")
        
        op = input("\nSeleccione una opción [Ej: 1]: ").strip()
        verificar_salida(op)
        
        if op == "1":
            ver_productos_por_categoria(db)
        elif op == "2":
            with TransaccionDB(gestor) as db_trans:
                agregar_nueva_categoria(db_trans)
        elif op == "3":
            with TransaccionDB(gestor) as db_trans:
                eliminar_producto(db_trans)
        elif op == "4":
            with TransaccionDB(gestor) as db_trans:
                eliminar_categoria(db_trans)
        elif op == "5":
            break
        else:
            depurar("Opción no válida en el menú de inventario.", "ADVER")
            pausar()