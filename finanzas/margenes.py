import math

from finanzas.periodo import (
    limpiar_pantalla, pausar, verificar_salida, VolverAlMenuException, depurar,
    encabezado, menu_opciones, tabla, mensaje_caja, dinero, marca_prompt,
    a_entero, es_si, validar_texto, LIMITE_NUMERICO,
)

def obtener_tabla_inventario(db, titulo="Productos disponibles en inventario:"):
    inventario = db.get("inventario", {})
    if not inventario:
        return mensaje_caja("El inventario está actualmente vacío.")
    filas = []
    for cod, p in inventario.items():
        stock = p.get("stock", 0)
        bajo = stock <= p.get("stock_min", 5)
        filas.append((cod, p.get("nombre", "?"), p.get("categoria", "General"),
                      (str(stock), "rojo" if bajo else "verde"), dinero(p.get("precio", 0))))
    return tabla(titulo, [("COD", 6, "izq"), ("NOMBRE", 20, "izq"), ("CATEGORÍA", 12, "izq"),
                          ("STOCK", 6, "der"), ("PRECIO", 10, "der")], filas)

def obtener_tabla_clientes(db, titulo="Clientes registrados:"):
    clientes = db.get("clientes", {})
    if not clientes:
        return mensaje_caja("No hay clientes registrados (se asignará 'Consumidor Final' si deja en blanco).")
    filas = []
    for id_c, c in clientes.items():
        filas.append((id_c, c.get("nombre", "?"), c.get("telefono", "N/A"), str(c.get("compras", 0))))
    return tabla(titulo, [("ID / RIF", 14, "izq"), ("NOMBRE", 20, "izq"),
                          ("TELÉFONO", 14, "izq"), ("COMPRAS", 8, "der")], filas)

def solicitar_con_aviso(mensaje, validador_tipo=str, permitir_vacio=False, header_extra=None, minimo=None):
    problema = None
    while True:
        limpiar_pantalla()
        encabezado("Escriba '0' o 'salir' en cualquier momento para volver al menú")
        if header_extra:
            print(header_extra)
            print()
        if problema:
            depurar(problema, "ADVER")   # El error se ve encima de la pregunta, sin pedir otro Enter
            print()
        entrada = input(marca_prompt() + mensaje).strip()
        verificar_salida(entrada)
        if not entrada:
            if permitir_vacio:
                return ""
            problema = "Este campo no puede estar vacío."
            continue
        try:
            if validador_tipo in (int, float):
                if "_" in entrada:
                    raise ValueError("Python acepta '_' en números; aquí no.")
                if validador_tipo == int:
                    valor = int(entrada)
                else:
                    if "," in entrada and "." not in entrada:
                        entrada = entrada.replace(",", ".")   # Acepta 15,50 además de 15.50
                    valor = float(entrada)
                    if not math.isfinite(valor):              # Rechaza nan e inf
                        raise ValueError("Valor no finito.")
            else:
                error_texto = validar_texto(entrada)
                if error_texto:
                    problema = error_texto
                    continue
                return " ".join(entrada.split())              # Quita espacios repetidos
        except ValueError:
            tipo_nombre = "un número entero válido" if validador_tipo == int else "un número válido (ej. 15.50)"
            problema = f"Por favor, ingrese {tipo_nombre}."
            continue
        if abs(valor) > LIMITE_NUMERICO:
            problema = f"El valor es demasiado grande (máximo {LIMITE_NUMERICO:,})."
            continue
        if minimo is not None and valor < minimo:
            problema = f"El valor debe ser mayor o igual a {minimo}."
            continue
        return valor

def seleccionar_o_crear_categoria(db, tipo="productos"):
    problema = None
    while True:
        limpiar_pantalla()
        key = "categorias" if tipo == "productos" else "categorias_gastos"
        default_vals = ["General", "Víveres", "Limpieza", "Bebidas"] if tipo == "productos" else ["Operativo", "Administrativo", "Mercancía", "Servicios"]
        categorias = db.get(key, default_vals)
        opciones = [(str(i), cat, "amarillo") for i, cat in enumerate(categorias, 1)]
        opciones.append((str(len(categorias) + 1), "[Crear una nueva categoría]", "verde"))
        opciones.append(("0", "Volver al Menú Principal", "gris"))
        encabezado("Escriba '0' o 'salir' para volver al menú")
        menu_opciones(f"Categorías de {'productos' if tipo == 'productos' else 'gastos'}", opciones)
        if problema:
            depurar(problema, "ADVER")
            problema = None
        opcion_input = input("\nSeleccione una opción o escriba el nombre de una nueva categoría: ").strip()
        verificar_salida(opcion_input)
        if opcion_input == "0":
            raise VolverAlMenuException()
        if opcion_input.isdigit():
            numero = a_entero(opcion_input)       # '²' es "dígito" para Python pero no es un número válido
            if numero is None:
                problema = "Opción inválida. Escriba un número de la lista."
                continue
            idx = numero - 1
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
                problema = f"La opción {numero} no está en la lista."
                continue
        else:
            nueva_cat = " ".join(opcion_input.split()).title()
            if not nueva_cat:
                problema = "Escriba un número de la lista o el nombre de una categoría."
                continue
            error_texto = validar_texto(nueva_cat, 30)
            if error_texto:
                problema = error_texto
                continue
            if nueva_cat not in categorias:
                categorias.append(nueva_cat)
                db[key] = categorias
            return nueva_cat

def agregar_producto(db):
    header_text = obtener_tabla_inventario(db, "Inventario actual (para referencia de códigos):")
    codigo = solicitar_con_aviso("Código del producto [Ej: P001]: ", header_extra=header_text).upper()
    if codigo in db["inventario"]:
        limpiar_pantalla()
        encabezado("Actualizar stock")
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
    costo = solicitar_con_aviso("Costo unitario de compra ($) [Ej: 3.50]: ", float, minimo=0)
    precio = solicitar_con_aviso("Precio unitario de venta ($) [Ej: 5.00]: ", float, minimo=0)
    stock = solicitar_con_aviso("Stock inicial [Ej: 20]: ", int, minimo=0)
    stock_min = solicitar_con_aviso("Stock mínimo para alerta [Ej: 5]: ", int, minimo=0)
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
    header_text = obtener_tabla_inventario(db, "Seleccione el producto a eliminar:")
    codigo = solicitar_con_aviso("Ingrese el código exacto del producto a eliminar: ", header_extra=header_text).upper()
    if codigo not in db["inventario"]:
        limpiar_pantalla()
        depurar(f"El producto con código '{codigo}' no existe en el inventario.", "ERROR")
        pausar()
        return
    prod = db["inventario"][codigo]
    limpiar_pantalla()
    encabezado("Eliminar producto")
    print(f"\nProducto seleccionado: {prod['nombre']} (Código: {codigo})")
    confirmacion = input("\n¿Estás seguro de eliminar este producto permanentemente? (s/n): ").strip().lower()
    verificar_salida(confirmacion)
    if es_si(confirmacion):
        del db["inventario"][codigo]
        limpiar_pantalla()
        depurar(f"Producto '{prod['nombre']}' eliminado con éxito.", "OK")
    else:
        limpiar_pantalla()
        depurar("Operación de eliminación cancelada.", "INFO")
    pausar()

def eliminar_categoria(db):
    limpiar_pantalla()
    categorias = db.get("categorias", ["General"])
    if len(categorias) <= 1:
        encabezado("Eliminar categoría de productos")
        depurar("No es posible eliminar todas las categorías. Debe existir al menos una ('General').", "ADVER")
        pausar()
        return
    encabezado("Eliminar categoría de productos")
    menu_opciones("Categorías disponibles", [(str(i), cat, "amarillo") for i, cat in enumerate(categorias, 1)])
    opcion = input("\nSeleccione el número de la categoría que desea eliminar: ").strip()
    verificar_salida(opcion)
    numero = a_entero(opcion)
    if numero is None:
        depurar("Operación cancelada.", "INFO")
        pausar()
        return
    idx = numero - 1
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
    if es_si(confirmacion):
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
    encabezado("Inventario clasificado por categorías")
    categorias = db.get("categorias", ["General"])
    inventario = db.get("inventario", {})
    if not inventario:
        print()
        print(mensaje_caja("El inventario está vacío."))
    else:
        hay_alerta = False
        for cat in categorias:
            print()
            prods = [(cod, p) for cod, p in inventario.items() if p.get("categoria", "General") == cat]
            if not prods:
                print(mensaje_caja(f"Categoría {cat.upper()}: sin productos.", "gris"))
                continue
            filas = []
            for cod, p in prods:
                bajo = p["stock"] <= p.get("stock_min", 5)
                hay_alerta = hay_alerta or bajo
                filas.append((cod, p["nombre"], (f"{p['stock']}{' !' if bajo else ''}", "rojo" if bajo else "verde"),
                              dinero(p.get("costo", 0)), dinero(p.get("precio", 0))))
            print(tabla(f"Categoría: {cat.upper()}",
                        [("COD", 6, "izq"), ("NOMBRE", 20, "izq"), ("STOCK", 7, "der"),
                         ("COSTO", 10, "der"), ("VENTA", 10, "der")], filas))
        if hay_alerta:
            print("\n ! = stock bajo (igual o menor al mínimo de alerta)")
    pausar()

def menu_inventario(gestor):
    from base import TransaccionDB
    while True:
        db = gestor.cargar()
        limpiar_pantalla()
        encabezado("Gestión de inventario")
        menu_opciones("Opciones", [
            ("1", "Ver Inventario por Categoría", "cyan"),
            ("2", "Agregar Nueva Categoría de Productos", "verde"),
            ("3", "Eliminar Producto", "rojo"),
            ("4", "Eliminar Categoría de Productos", "rojo"),
            ("5", "Volver al Menú Principal", "gris"),
        ])
        
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
