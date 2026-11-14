import sqlite3
from datetime import datetime
import os
from finanzas.periodo import limpiar_pantalla

class SistemaInventario:
    def __init__(self, db_name="erp_empresa_v2.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._inicializar_tablas()

    def _inicializar_tablas(self):
        """Crea la estructura de tablas incluyendo costos unitarios e impacto financiero."""
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS almacenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                ubicacion TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                costo_unitario REAL NOT NULL CHECK(costo_unitario >= 0),
                stock_minimo INTEGER NOT NULL DEFAULT 5
            );

            CREATE TABLE IF NOT EXISTS inventario (
                almacen_id INTEGER,
                producto_id INTEGER,
                cantidad INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (almacen_id, producto_id),
                FOREIGN KEY (almacen_id) REFERENCES almacenes(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL,
                almacen_origen_id INTEGER,
                almacen_destino_id INTEGER,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                costo_unitario REAL NOT NULL,
                impacto_financiero REAL NOT NULL,
                motivo TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );
        ''')
        self.conn.commit()

    def crear_almacen(self, nombre, ubicacion):
        try:
            self.cursor.execute(
                "INSERT INTO almacenes (nombre, ubicacion) VALUES (?, ?)",
                (nombre.strip(), ubicacion.strip())
            )
            self.conn.commit()
            print(f"\n[OK] Almacén '{nombre}' registrado con éxito.")
        except sqlite3.IntegrityError:
            limpiar_pantalla()
            print(f"\n[ERROR] Ya existe un almacén con el nombre '{nombre}'.")

    def crear_producto(self, sku, nombre, costo_unitario, stock_minimo):
        try:
            self.cursor.execute(
                "INSERT INTO productos (sku, nombre, costo_unitario, stock_minimo) VALUES (?, ?, ?, ?)",
                (sku.strip().upper(), nombre.strip(), float(costo_unitario), int(stock_minimo))
            )
            self.conn.commit()
            print(f"\n[OK] Producto '{nombre}' (SKU: {sku.upper()}) creado con costo ${costo_unitario:,.2f}.")
        except sqlite3.IntegrityError:
            limpiar_pantalla()
            print(f"\n[ERROR] El SKU '{sku}' ya está registrado.")

    def _obtener_costo_producto(self, producto_id):
        self.cursor.execute("SELECT costo_unitario FROM productos WHERE id = ?", (producto_id,))
        fila = self.cursor.fetchone()
        if not fila:
            limpiar_pantalla()
            raise ValueError(f"El producto con ID {producto_id} no existe.")
        return fila[0]

    def _obtener_stock_actual(self, almacen_id, producto_id):
        self.cursor.execute(
            "SELECT cantidad FROM inventario WHERE almacen_id = ? AND producto_id = ?",
            (almacen_id, producto_id)
        )
        fila = self.cursor.fetchone()
        return fila[0] if fila else 0

    def _actualizar_stock_directo(self, almacen_id, producto_id, delta_cantidad):
        stock_actual = self._obtener_stock_actual(almacen_id, producto_id)
        nuevo_stock = stock_actual + delta_cantidad
        if nuevo_stock < 0:
            raise ValueError(f"Stock insuficiente (Actual: {stock_actual}, Requerido: {abs(delta_cantidad)}).")

        self.cursor.execute('''
            INSERT INTO inventario (almacen_id, producto_id, cantidad)
            VALUES (?, ?, ?)
            ON CONFLICT(almacen_id, producto_id)
            DO UPDATE SET cantidad = ?
        ''', (almacen_id, producto_id, nuevo_stock, nuevo_stock))

    def registrar_ajuste_o_merma(self, almacen_id, producto_id, cantidad_delta, tipo, motivo):
        try:
            costo_unit = self._obtener_costo_producto(producto_id)
            self._actualizar_stock_directo(almacen_id, producto_id, cantidad_delta)
            
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            impacto_financiero = cantidad_delta * costo_unit
            
            self.cursor.execute('''
                INSERT INTO movimientos 
                (fecha, tipo, almacen_origen_id, almacen_destino_id, producto_id, cantidad, costo_unitario, impacto_financiero, motivo)
                VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?)
            ''', (fecha, tipo, almacen_id, producto_id, cantidad_delta, costo_unit, impacto_financiero, motivo))
            
            self.conn.commit()
            limpiar_pantalla()
            print(f"\n[OK] {tipo} registrado ({cantidad_delta:+} uds | Impacto contable: ${impacto_financiero:+,.2f}).")
        except ValueError as e:
            limpiar_pantalla()
            self.conn.rollback()
            print(f"\n[ERROR DE OPERACIÓN] {e}")
        except sqlite3.Error as e:
            limpiar_pantalla()
            self.conn.rollback()
            print(f"\n[ERROR DE BASE DE DATOS] {e}")

    def transferir_mercancia(self, origen_id, destino_id, producto_id, cantidad, motivo="Transferencia entre sedes"):
        if origen_id == destino_id:
            limpiar_pantalla()
            print("\n[ERROR] El almacén de origen y destino no pueden ser el mismo.")
            return
        if cantidad <= 0:
            limpiar_pantalla()
            print("\n[ERROR] La cantidad a transferir debe ser mayor a 0.")
            return

        try:
            costo_unit = self._obtener_costo_producto(producto_id)
            self._actualizar_stock_directo(origen_id, producto_id, -cantidad)
            self._actualizar_stock_directo(destino_id, producto_id, cantidad)
            
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            valor_trasladado = cantidad * costo_unit
            
            self.cursor.execute('''
                INSERT INTO movimientos 
                (fecha, tipo, almacen_origen_id, almacen_destino_id, producto_id, cantidad, costo_unitario, impacto_financiero, motivo)
                VALUES (?, 'TRANSFERENCIA', ?, ?, ?, ?, ?, ?, ?)
            ''', (fecha, origen_id, destino_id, producto_id, cantidad, costo_unit, valor_trasladado, motivo))

            self.conn.commit()
            limpiar_pantalla()
            print(f"\n[OK] Transferencia exitosa de {cantidad} uds (Valor en traslado: ${valor_trasladado:,.2f}).")
        except ValueError as e:
            limpiar_pantalla()
            self.conn.rollback()
            print(f"\n[ERROR EN TRANSFERENCIA] {e}")
        except sqlite3.Error as e:
            limpiar_pantalla()
            self.conn.rollback()
            print(f"\n[ERROR CRÍTICO] {e}")

    @staticmethod
    def _imprimir_tabla(encabezados, filas, titulo=""):
        if titulo:
            print(f"\n=== {titulo.upper()} ===")
        if not filas:
            print("  (No hay registros para mostrar)")
            return

        anchos = [len(str(h)) for h in encabezados]
        for fila in filas:
            for i, valor in enumerate(fila):
                anchos[i] = max(anchos[i], len(str(valor if valor is not None else "N/A")))

        linea_sep = "+-" + "-+-".join("-" * w for w in anchos) + "-+"
        formato_fila = "| " + " | ".join(f"{{:<{w}}}" for w in anchos) + " |"

        print(linea_sep)
        print(formato_fila.format(*encabezados))
        print(linea_sep)
        for fila in filas:
            fila_limpia = [str(v if v is not None else "-") for v in fila]
            print(formato_fila.format(*fila_limpia))
        print(linea_sep)

    def ver_almacenes(self):
        self.cursor.execute("SELECT id, nombre, ubicacion FROM almacenes ORDER BY id")
        self._imprimir_tabla(["ID", "Nombre Almacén", "Ubicación"], self.cursor.fetchall(), "Catálogo de Almacenes")

    def ver_productos(self):
        self.cursor.execute("SELECT id, sku, nombre, printf('$%.2f', costo_unitario), stock_minimo FROM productos ORDER BY id")
        self._imprimir_tabla(["ID", "SKU", "Producto", "Costo Unit.", "Stock Mínimo"], self.cursor.fetchall(), "Catálogo de Productos")

    def ver_inventario_general(self, almacen_id=None):
        query = '''
            SELECT a.id, a.nombre, p.sku, p.nombre, i.cantidad, 
                   printf('$%.2f', p.costo_unitario),
                   printf('$%.2f', i.cantidad * p.costo_unitario) AS valor_total,
                   CASE WHEN i.cantidad <= p.stock_minimo THEN '¡ALERTA BAJO!' ELSE 'OK' END AS estado
            FROM inventario i
            JOIN almacenes a ON i.almacen_id = a.id
            JOIN productos p ON i.producto_id = p.id
        '''
        params = ()
        if almacen_id:
            query += " WHERE a.id = ?"
            params = (almacen_id,)
        query += " ORDER BY a.nombre, p.nombre"

        self.cursor.execute(query, params)
        encabezados = ["ID Alm.", "Almacén", "SKU", "Producto", "Stock", "Costo Unit.", "Valor Total", "Estado"]
        self._imprimir_tabla(encabezados, self.cursor.fetchall(), "Inventario Físico y Valorizado")

    def ver_alertas_stock_minimo(self):
        query = '''
            SELECT a.nombre, p.sku, p.nombre, COALESCE(i.cantidad, 0) as cant, p.stock_minimo,
                   (p.stock_minimo - COALESCE(i.cantidad, 0)) as faltante,
                   printf('$%.2f', (p.stock_minimo - COALESCE(i.cantidad, 0)) * p.costo_unitario) as costo_reposicion
            FROM productos p
            CROSS JOIN almacenes a
            LEFT JOIN inventario i ON i.producto_id = p.id AND i.almacen_id = a.id
            WHERE COALESCE(i.cantidad, 0) <= p.stock_minimo
            ORDER BY faltante DESC
        '''
        self.cursor.execute(query)
        encabezados = ["Almacén", "SKU", "Producto", "Stock", "Mínimo", "Déficit", "Costo Reposición Min."]
        self._imprimir_tabla(encabezados, self.cursor.fetchall(), "Alertas de Stock Mínimo y Presupuesto de Compra")

    def ver_historial_movimientos(self):
        query = '''
            SELECT m.id, m.fecha, m.tipo, 
                   ao.nombre as origen, ad.nombre as destino, 
                   p.sku, m.cantidad, 
                   printf('$%.2f', m.costo_unitario),
                   printf('$%.2f', m.impacto_financiero),
                   m.motivo
            FROM movimientos m
            JOIN productos p ON m.producto_id = p.id
            LEFT JOIN almacenes ao ON m.almacen_origen_id = ao.id
            LEFT JOIN almacenes ad ON m.almacen_destino_id = ad.id
            ORDER BY m.id DESC LIMIT 30
        '''
        self.cursor.execute(query)
        encabezados = ["ID", "Fecha", "Tipo", "Origen", "Destino", "SKU", "Cant.", "Costo U.", "Impacto ($)", "Motivo"]
        self._imprimir_tabla(encabezados, self.cursor.fetchall(), "Kardex Valorizado (Últimos 30 Movimientos)")

    def reporte_contable_valor_inventario(self):
        query_almacenes = '''
            SELECT a.id, a.nombre, 
                   COALESCE(SUM(i.cantidad), 0) AS total_unidades,
                   printf('$%.2f', COALESCE(SUM(i.cantidad * p.costo_unitario), 0)) AS valor_almacen
            FROM almacenes a
            LEFT JOIN inventario i ON a.id = i.almacen_id
            LEFT JOIN productos p ON i.producto_id = p.id
            GROUP BY a.id, a.nombre
            ORDER BY a.id
        '''
        self.cursor.execute(query_almacenes)
        encabezados = ["ID Almacén", "Sede / Bodega", "Unidades Totales", "Valor Monetario (Activo)"]
        self._imprimir_tabla(encabezados, self.cursor.fetchall(), "Balance de Inventario por Centro de Costo")

        self.cursor.execute('''
            SELECT COALESCE(SUM(i.cantidad * p.costo_unitario), 0)
            FROM inventario i
            JOIN productos p ON i.producto_id = p.id
        ''')
        gran_total = self.cursor.fetchone()[0]
        print(f"\n  >>> VALOR TOTAL DEL INVENTARIO (ACTIVO CIRCULANTE): ${gran_total:,.2f} <<<")

    def reporte_contable_mermas(self):
        query_mermas = '''
            SELECT m.id, m.fecha, a.nombre, p.sku, p.nombre, 
                   ABS(m.cantidad) AS uds_perdidas,
                   printf('$%.2f', m.costo_unitario),
                   printf('$%.2f', ABS(m.impacto_financiero)) AS perdida_monetaria,
                   m.motivo
            FROM movimientos m
            JOIN almacenes a ON m.almacen_origen_id = a.id
            JOIN productos p ON m.producto_id = p.id
            WHERE m.tipo = 'MERMA'
            ORDER BY m.fecha DESC
        '''
        self.cursor.execute(query_mermas)
        encabezados = ["ID Mov.", "Fecha", "Almacén", "SKU", "Producto", "Uds. Perdidas", "Costo Unit.", "Pérdida ($)", "Motivo"]
        self._imprimir_tabla(encabezados, self.cursor.fetchall(), "Detalle de Mermas y Pérdidas de Inventario")

        self.cursor.execute('''
            SELECT COALESCE(SUM(ABS(cantidad)), 0), COALESCE(SUM(ABS(impacto_financiero)), 0)
            FROM movimientos
            WHERE tipo = 'MERMA'
        ''')
        uds_totales, perdida_total = self.cursor.fetchone()
        print(f"\n  >>> TOTAL UNIDADES DADAS DE BAJA: {uds_totales} uds.")
        print(f"  >>> IMPACTO CONTABLE TOTAL POR MERMAS (GASTO/PÉRDIDA): -${perdida_total:,.2f} <<<")