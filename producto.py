import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


# ==========================================
# CONEXIÓN Y FUNCIONES DE LA BASE DE DATOS
# ==========================================
def conectar_db():
    """Crea la conexión y la tabla si no existen."""
    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """
    )
    conexion.commit()
    conexion.close()


def insertar_producto():
    """Adiciona un nuevo producto."""
    if (
        var_nombre.get() == ""
        or var_precio.get() == ""
        or var_stock.get() == ""
    ):
        messagebox.showwarning("Campos vacíos", "Por favor llena todos los campos")
        return

    try:
        conexion = sqlite3.connect("inventario.db")
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
            (var_nombre.get(), float(var_precio.get()), int(var_stock.get())),
        )
        conexion.commit()
        conexion.close()
        messagebox.showinfo("Éxito", "Producto adicionado correctamente")
        limpiar_campos()
        mostrar_datos()
    except ValueError:
        messagebox.showerror(
            "Error de datos", "Precio debe ser número y Stock debe ser entero"
        )


def mostrar_datos():
    """Consulta todos los datos y los vuelca en la tabla de la interfaz."""
    # Limpiar tabla visual
    for fila in tabla.get_children():
        tabla.delete(fila)

    conexion = sqlite3.connect("inventario.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos")
    filas = cursor.fetchall()

    for fila in filas:
        tabla.insert("", tk.END, values=fila)

    conexion.close()


def eliminar_producto():
    """Elimina el producto seleccionado."""
    if var_id.get() == "":
        messagebox.showwarning(
            "Selección", "Por favor, selecciona un producto de la tabla"
        )
        return

    confirmar = messagebox.askyesno(
        "Confirmar", "¿Estás seguro de eliminar este producto?"
    )
    if confirmar:
        conexion = sqlite3.connect("inventario.db")
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (var_id.get(),))
        conexion.commit()
        conexion.close()
        messagebox.showinfo("Éxito", "Producto eliminado")
        limpiar_campos()
        mostrar_datos()


def modificar_producto():
    """Modifica el producto seleccionado con los nuevos datos de los campos."""
    if var_id.get() == "":
        messagebox.showwarning(
            "Selección", "Por favor, selecciona un producto para modificar"
        )
        return

    try:
        conexion = sqlite3.connect("inventario.db")
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE id = ?",
            (
                var_nombre.get(),
                float(var_precio.get()),
                int(var_stock.get()),
                var_id.get(),
            ),
        )
        conexion.commit()
        conexion.close()
        messagebox.showinfo("Éxito", "Producto modificado correctamente")
        limpiar_campos()
        mostrar_datos()
    except ValueError:
        messagebox.showerror(
            "Error de datos", "Precio debe ser número y Stock debe ser entero"
        )


def seleccionar_fila(event):
    """Al hacer clic en la tabla, pasa los datos a los campos de texto."""
    item_seleccionado = tabla.focus()
    if not item_seleccionado:
        return

    valores = tabla.item(item_seleccionado, "values")

    # Llenar variables
    var_id.set(valores[0])
    var_nombre.set(valores[1])
    var_precio.set(valores[2])
    var_stock.set(valores[3])


def limpiar_campos():
    """Resetea los formularios visuales."""
    var_id.set("")
    var_nombre.set("")
    var_precio.set("")
    var_stock.set("")


# ==========================================
# INTERFAZ GRÁFICA (TKINTER)
# ==========================================
conectar_db()  # Inicializar BD

ventana = tk.Tk()
ventana.title("CRUD Python + SQL (SQLite)")
ventana.geometry("700x450")

# Variables de control
var_id = tk.StringVar()
var_nombre = tk.StringVar()
var_precio = tk.StringVar()
var_stock = tk.StringVar()

# Contenedor de Formulario (Izquierda)
frame_form = tk.LabelFrame(ventana, text=" Datos del Producto ", padx=10, pady=10)
frame_form.place(x=20, y=20, width=260, height=230)

tk.Label(frame_form, text="ID (Auto):").grid(row=0, column=0, sticky="w", pady=5)
tk.Entry(frame_form, textvariable=var_id, state="readonly", width=20).grid(
    row=0, column=1, pady=5
)

tk.Label(frame_form, text="Nombre:").grid(row=1, column=0, sticky="w", pady=5)
tk.Entry(frame_form, textvariable=var_nombre, width=20).grid(
    row=1, column=1, pady=5
)

tk.Label(frame_form, text="Precio ($):").grid(row=2, column=0, sticky="w", pady=5)
tk.Entry(frame_form, textvariable=var_precio, width=20).grid(
    row=2, column=1, pady=5
)

tk.Label(frame_form, text="Stock:").grid(row=3, column=0, sticky="w", pady=5)
tk.Entry(frame_form, textvariable=var_stock, width=20).grid(
    row=3, column=1, pady=5
)

# Contenedor de Botones (Acciones)
frame_botones = tk.Frame(ventana)
frame_botones.place(x=20, y=270, width=260, height=150)

tk.Button(
    frame_botones,
    text="Adicionar (C)",
    bg="#4CAF50",
    fg="white",
    command=insertar_producto,
    width=12,
).grid(row=0, column=0, padx=5, pady=5)
tk.Button(
    frame_botones,
    text="Modificar (U)",
    bg="#2196F3",
    fg="white",
    command=modificar_producto,
    width=12,
).grid(row=0, column=1, padx=5, pady=5)
tk.Button(
    frame_botones,
    text="Eliminar (D)",
    bg="#f44336",
    fg="white",
    command=eliminar_producto,
    width=12,
).grid(row=1, column=0, padx=5, pady=5)
tk.Button(
    frame_botones,
    text="Limpiar Campos",
    bg="#ff9800",
    fg="white",
    command=limpiar_campos,
    width=12,
).grid(row=1, column=1, padx=5, pady=5)

# Contenedor de Visualización / Consulta (Derecha)
frame_tabla = tk.LabelFrame(
    ventana, text=" Registros Guardados (R) ", padx=10, pady=10
)
frame_tabla.place(x=300, y=20, width=380, height=400)

# Tabla (Treeview)
tabla = ttk.Treeview(
    frame_tabla, columns=("ID", "Nombre", "Precio", "Stock"), show="headings"
)
tabla.heading("ID", text="ID")
tabla.heading("Nombre", text="Nombre")
tabla.heading("Precio", text="Precio")
tabla.heading("Stock", text="Stock")

# Configurar ancho de columnas
tabla.column("ID", width=40, anchor="center")
tabla.column("Nombre", width=140)
tabla.column("Precio", width=80, anchor="center")
tabla.column("Stock", width=80, anchor="center")

tabla.pack(fill="both", expand=True)
tabla.bind("<<TreeviewSelect>>", seleccionar_fila)

# Cargar los datos por primera vez al abrir
mostrar_datos()

ventana.mainloop()
