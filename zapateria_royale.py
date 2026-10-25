"""Sistema de Gestión de Zapaterías Royal - versión con interfaz gráfica.

Python puro: solo usa la librería estándar (tkinter viene incluido).
Ejecutar con:  python zapateria_royal_gui.py
"""

import json
import math
import os
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, List, Optional, Tuple

# Rango de tallas en México (se incluyen medias tallas, ej. 25.5)
TALLA_MIN = 22
TALLA_MAX = 33

# Archivo donde se guardan automáticamente los datos (junto a este programa).
# Es el mismo archivo que usa la versión de consola.
ARCHIVO_DATOS = Path(__file__).resolve().parent / "datos_zapateria.json"


def formatear_talla(valor: float) -> str:
    return str(int(valor)) if valor == int(valor) else f"{valor:.1f}"


TALLAS: List[str] = [formatear_talla(t / 2) for t in range(TALLA_MIN * 2, TALLA_MAX * 2 + 1)]


def dinero(valor: float) -> str:
    return f"${valor:,.2f}"


# ----------------------------------------------------------------------
# Modelos
# ----------------------------------------------------------------------
@dataclass
class Existencia:
    talla: str
    color: str
    cantidad: int
    precio: float


@dataclass
class Venta:
    zapato: str
    talla: str
    color: str
    cantidad: int
    precio_unitario: float
    descuento: float  # porcentaje aplicado en el momento de la venta
    total: float


# ----------------------------------------------------------------------
# Lógica del negocio (sin interfaz; lanza ValueError con mensajes claros)
# ----------------------------------------------------------------------
class Zapateria:
    def __init__(self) -> None:
        self.inventario: Dict[str, List[Existencia]] = {}
        self.ventas: List[Venta] = []
        self.descuento: float = 0.0  # porcentaje
        self.error_guardado: Optional[str] = None  # último error al escribir en disco
        self.aviso_carga: Optional[str] = None     # problema al leer el archivo al iniciar
        self.cargar()

    # ---------------- Guardado en disco ----------------
    def guardar(self) -> None:
        """Escribe todos los datos en ARCHIVO_DATOS (primero a un temporal, para no corromperlo)."""
        datos = {
            "inventario": {n: [asdict(e) for e in es] for n, es in self.inventario.items()},
            "ventas": [asdict(v) for v in self.ventas],
            "descuento": self.descuento,
        }
        temporal = ARCHIVO_DATOS.with_name(ARCHIVO_DATOS.name + ".tmp")
        try:
            with open(temporal, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
            os.replace(temporal, ARCHIVO_DATOS)
            self.error_guardado = None
        except OSError as error:
            self.error_guardado = str(error)

    def cargar(self) -> None:
        """Lee los datos guardados, si existen."""
        if not ARCHIVO_DATOS.exists():
            return
        try:
            with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
                datos = json.load(archivo)
            inventario = {n: [Existencia(**e) for e in es] for n, es in datos["inventario"].items()}
            ventas = [Venta(**v) for v in datos["ventas"]]
            descuento = float(datos["descuento"])
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            respaldo = ARCHIVO_DATOS.with_name(ARCHIVO_DATOS.name + ".bak")
            try:
                os.replace(ARCHIVO_DATOS, respaldo)
            except OSError:
                pass
            self.aviso_carga = (f"El archivo de datos estaba dañado ({error}).\n"
                                f"Se guardó una copia en {respaldo.name} y se inicia vacío.")
            return
        self.inventario, self.ventas, self.descuento = inventario, ventas, descuento

    @staticmethod
    def _buscar(existencias: List[Existencia], talla: str, color: str) -> Optional[Existencia]:
        for e in existencias:
            if e.talla == talla and e.color.lower() == color.lower():
                return e
        return None

    @staticmethod
    def _validar_precio(precio: float) -> None:
        if not math.isfinite(precio) or precio < 0:
            raise ValueError("El precio debe ser un número mayor o igual a 0.")

    def agregar_zapato(self, nombre: str, color: str, precio: float, cantidades: Dict[str, int]) -> None:
        nombre, color = nombre.strip(), color.strip()
        if not nombre:
            raise ValueError("Escriba el nombre del zapato.")
        if not color:
            raise ValueError("Escriba el color.")
        self._validar_precio(precio)
        cantidades = {t: c for t, c in cantidades.items() if c > 0}
        if not cantidades:
            raise ValueError("Indique cuántos tenis hay en al menos una talla.")

        existencias = self.inventario.setdefault(nombre, [])
        for talla, cantidad in cantidades.items():
            actual = self._buscar(existencias, talla, color)
            if actual:
                actual.cantidad += cantidad
                actual.precio = precio
            else:
                existencias.append(Existencia(talla, color, cantidad, precio))
        self.guardar()

    def actualizar_existencia(self, nombre: str, existencia: Existencia,
                              talla: str, color: str, cantidad: int, precio: float,
                              nuevo_nombre: Optional[str] = None) -> None:
        """Actualiza una fila. Si cambia el nombre, se renombra el zapato con todas sus tallas."""
        nuevo_nombre = (nombre if nuevo_nombre is None else nuevo_nombre).strip()
        if not nuevo_nombre:
            raise ValueError("Escriba el nombre del zapato.")
        if nuevo_nombre != nombre and nuevo_nombre in self.inventario:
            raise ValueError("Ya existe un zapato con ese nombre.")
        color = color.strip()
        if not color:
            raise ValueError("Escriba el color.")
        if talla not in TALLAS:
            raise ValueError(f"La talla debe estar entre {TALLA_MIN} y {TALLA_MAX}.")
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self._validar_precio(precio)
        otra = self._buscar(self.inventario[nombre], talla, color)
        if otra is not None and otra is not existencia:
            raise ValueError("Ya existe esa talla en ese color.")
        existencia.talla, existencia.color = talla, color
        existencia.cantidad, existencia.precio = cantidad, precio
        if nuevo_nombre != nombre:
            self.inventario[nuevo_nombre] = self.inventario.pop(nombre)
        self.guardar()

    def eliminar_existencia(self, nombre: str, existencia: Existencia) -> None:
        self.inventario[nombre].remove(existencia)
        if not self.inventario[nombre]:
            del self.inventario[nombre]
        self.guardar()

    def vender(self, nombre: str, existencia: Existencia, cantidad: int) -> Venta:
        if cantidad < 1:
            raise ValueError("La cantidad vendida debe ser al menos 1.")
        if existencia.cantidad < cantidad:
            raise ValueError(f"No hay suficiente inventario (disponible: {existencia.cantidad}).")
        existencia.cantidad -= cantidad
        total = existencia.precio * cantidad * (1 - self.descuento / 100)
        venta = Venta(nombre, existencia.talla, existencia.color, cantidad,
                      existencia.precio, self.descuento, total)
        self.ventas.append(venta)
        self.guardar()
        return venta

    def establecer_descuento(self, descuento: float) -> None:
        if not math.isfinite(descuento) or not (0 <= descuento <= 100):
            raise ValueError("El descuento debe estar entre 0 y 100.")
        self.descuento = descuento
        self.guardar()


# ----------------------------------------------------------------------
# Interfaz gráfica
# ----------------------------------------------------------------------
def crear_tabla(padre, columnas: List[Tuple[str, str, int]], alto: int = 8) -> ttk.Treeview:
    """Crea un Treeview con barra de desplazamiento. columnas = [(id, título, ancho)]."""
    marco = ttk.Frame(padre)
    marco.pack(fill="both", expand=True, pady=(8, 0))
    tabla = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", height=alto)
    for ident, titulo, ancho in columnas:
        tabla.heading(ident, text=titulo)
        tabla.column(ident, width=ancho, anchor="center")
    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return tabla


def leer_precio(texto: str) -> float:
    try:
        valor = float(texto.strip().replace(",", "."))
    except ValueError:
        raise ValueError("El precio debe ser un número.")
    return valor


def leer_cantidad(texto: str, etiqueta: str = "cantidad") -> int:
    texto = texto.strip()
    if not texto:
        return 0
    try:
        valor = int(texto)
    except ValueError:
        raise ValueError(f"La {etiqueta} debe ser un número entero.")
    if valor < 0:
        raise ValueError(f"La {etiqueta} no puede ser negativa.")
    return valor


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Zapaterías Royal")
        self.geometry("920x680")
        self.minsize(840, 600)

        self.negocio = Zapateria()
        self._filas: Dict[str, Tuple[str, Existencia]] = {}  # iid de la tabla -> (nombre, existencia)
        self._variantes: List[Existencia] = []                # opciones del combo de ventas

        ttk.Label(self, text=f"Los datos se guardan automáticamente en: {ARCHIVO_DATOS}",
                  foreground="gray").pack(side="bottom", anchor="w", padx=10, pady=(0, 6))
        pestañas = ttk.Notebook(self)
        pestañas.pack(fill="both", expand=True, padx=8, pady=8)
        self._crear_inventario(pestañas)
        self._crear_ventas(pestañas)
        self._crear_reportes(pestañas)
        self._crear_configuracion(pestañas)
        self.v_descuento.set(f"{self.negocio.descuento:g}")
        self.lbl_descuento.config(text=f"Descuento actual: {self.negocio.descuento:g}%")
        self.refrescar()
        if self.negocio.aviso_carga:
            messagebox.showwarning("Datos dañados", self.negocio.aviso_carga)

    # ---------------- Inventario ----------------
    def _crear_inventario(self, pestañas: ttk.Notebook) -> None:
        tab = ttk.Frame(pestañas, padding=10)
        pestañas.add(tab, text="Inventario")

        form = ttk.LabelFrame(tab, text="Agregar zapato", padding=10)
        form.pack(fill="x")

        self.v_nombre, self.v_color, self.v_precio = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for col, (texto, var, ancho) in enumerate([("Nombre", self.v_nombre, 22),
                                                   ("Color", self.v_color, 14),
                                                   ("Precio", self.v_precio, 10)]):
            ttk.Label(form, text=texto).grid(row=0, column=col * 2, sticky="e", padx=(8, 2))
            ttk.Entry(form, textvariable=var, width=ancho).grid(row=0, column=col * 2 + 1, pady=3)

        tallas = ttk.LabelFrame(form, text=f"Cuántos tenis hay en cada talla (MX {TALLA_MIN} a {TALLA_MAX})", padding=6)
        tallas.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 0))
        self.v_cant: Dict[str, tk.StringVar] = {}
        for i, talla in enumerate(TALLAS):
            fila, col = divmod(i, 6)
            celda = ttk.Frame(tallas)
            celda.grid(row=fila, column=col, padx=8, pady=3)
            ttk.Label(celda, text=f"Talla {talla}", width=9).pack(side="left")
            var = tk.StringVar(value="0")
            self.v_cant[talla] = var
            ttk.Spinbox(celda, from_=0, to=9999, textvariable=var, width=5).pack(side="left")

        botones = ttk.Frame(form)
        botones.grid(row=2, column=0, columnspan=6, sticky="e", pady=(8, 0))
        ttk.Button(botones, text="Limpiar", command=self._limpiar_formulario).pack(side="left", padx=4)
        ttk.Button(botones, text="Agregar al inventario", command=self._agregar).pack(side="left", padx=4)

        self.tabla_inv = crear_tabla(tab, [("nombre", "Zapato", 220), ("talla", "Talla", 70),
                                           ("color", "Color", 130), ("cantidad", "Cantidad", 90),
                                           ("precio", "Precio", 110)], alto=9)
        acciones = ttk.Frame(tab)
        acciones.pack(fill="x", pady=(8, 0))
        ttk.Button(acciones, text="Modificar seleccionado", command=self._modificar).pack(side="left")
        ttk.Button(acciones, text="Eliminar seleccionado", command=self._eliminar).pack(side="left", padx=6)

    def _limpiar_formulario(self) -> None:
        for var in (self.v_nombre, self.v_color, self.v_precio):
            var.set("")
        for var in self.v_cant.values():
            var.set("0")

    def _agregar(self) -> None:
        try:
            precio = leer_precio(self.v_precio.get())
            cantidades = {t: leer_cantidad(v.get(), f"cantidad de la talla {t}") for t, v in self.v_cant.items()}
            self.negocio.agregar_zapato(self.v_nombre.get(), self.v_color.get(), precio, cantidades)
        except ValueError as error:
            messagebox.showwarning("Revise los datos", str(error))
            return
        nombre = self.v_nombre.get().strip()
        self._limpiar_formulario()
        self.refrescar()
        messagebox.showinfo("Listo", f"Zapato {nombre} agregado al inventario.")

    def _seleccionado(self) -> Optional[Tuple[str, Existencia]]:
        seleccion = self.tabla_inv.selection()
        if not seleccion:
            messagebox.showinfo("Seleccione una fila", "Primero seleccione un zapato de la tabla.")
            return None
        return self._filas[seleccion[0]]

    def _modificar(self) -> None:
        elegido = self._seleccionado()
        if not elegido:
            return
        nombre, existencia = elegido

        ventana = tk.Toplevel(self)
        ventana.title(f"Modificar {nombre}")
        ventana.resizable(False, False)
        ventana.transient(self)
        marco = ttk.Frame(ventana, padding=14)
        marco.pack()

        v_nombre = tk.StringVar(value=nombre)
        v_talla = tk.StringVar(value=existencia.talla)
        v_color = tk.StringVar(value=existencia.color)
        v_cantidad = tk.StringVar(value=str(existencia.cantidad))
        v_precio = tk.StringVar(value=f"{existencia.precio:.2f}")

        ttk.Label(marco, text="Nombre").grid(row=0, column=0, sticky="e", pady=4, padx=4)
        ttk.Entry(marco, textvariable=v_nombre, width=24).grid(row=0, column=1, sticky="w")
        ttk.Label(marco, text="(si lo cambia, se renombran todas las tallas de este zapato)",
                  foreground="gray").grid(row=1, column=0, columnspan=2, sticky="w", padx=4)
        ttk.Label(marco, text="Talla").grid(row=2, column=0, sticky="e", pady=4, padx=4)
        ttk.Combobox(marco, textvariable=v_talla, values=TALLAS, state="readonly", width=8).grid(row=2, column=1, sticky="w")
        ttk.Label(marco, text="Color").grid(row=3, column=0, sticky="e", pady=4, padx=4)
        ttk.Entry(marco, textvariable=v_color, width=18).grid(row=3, column=1, sticky="w")
        ttk.Label(marco, text="Cantidad").grid(row=4, column=0, sticky="e", pady=4, padx=4)
        ttk.Spinbox(marco, from_=0, to=9999, textvariable=v_cantidad, width=8).grid(row=4, column=1, sticky="w")
        ttk.Label(marco, text="Precio").grid(row=5, column=0, sticky="e", pady=4, padx=4)
        ttk.Entry(marco, textvariable=v_precio, width=12).grid(row=5, column=1, sticky="w")

        def guardar() -> None:
            try:
                self.negocio.actualizar_existencia(
                    nombre, existencia, v_talla.get(), v_color.get(),
                    leer_cantidad(v_cantidad.get()), leer_precio(v_precio.get()),
                    nuevo_nombre=v_nombre.get())
            except ValueError as error:
                messagebox.showwarning("Revise los datos", str(error), parent=ventana)
                return
            ventana.destroy()
            self.refrescar()

        ttk.Button(marco, text="Guardar", command=guardar).grid(row=6, column=0, columnspan=2, pady=(10, 0))
        ventana.grab_set()

    def _eliminar(self) -> None:
        elegido = self._seleccionado()
        if not elegido:
            return
        nombre, existencia = elegido
        if messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}, talla {existencia.talla}, {existencia.color}?"):
            self.negocio.eliminar_existencia(nombre, existencia)
            self.refrescar()

    # ---------------- Ventas ----------------
    def _crear_ventas(self, pestañas: ttk.Notebook) -> None:
        tab = ttk.Frame(pestañas, padding=20)
        pestañas.add(tab, text="Ventas")
        form = ttk.LabelFrame(tab, text="Registrar venta", padding=14)
        form.pack(fill="x")

        self.v_venta_zapato, self.v_venta_variante = tk.StringVar(), tk.StringVar()
        self.v_venta_cantidad = tk.StringVar(value="1")

        ttk.Label(form, text="Zapato").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.combo_zapato = ttk.Combobox(form, textvariable=self.v_venta_zapato, state="readonly", width=30)
        self.combo_zapato.grid(row=0, column=1, sticky="w")
        self.combo_zapato.bind("<<ComboboxSelected>>", lambda _e: self._cargar_variantes())

        ttk.Label(form, text="Talla y color").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.combo_variante = ttk.Combobox(form, textvariable=self.v_venta_variante, state="readonly", width=40)
        self.combo_variante.grid(row=1, column=1, sticky="w")
        self.combo_variante.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_total())

        ttk.Label(form, text="Cantidad").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        ttk.Spinbox(form, from_=1, to=9999, textvariable=self.v_venta_cantidad, width=8,
                    command=self._actualizar_total).grid(row=2, column=1, sticky="w")
        self.v_venta_cantidad.trace_add("write", lambda *_a: self._actualizar_total())

        self.lbl_total = ttk.Label(form, text="Total: $0.00", font=("TkDefaultFont", 13, "bold"))
        self.lbl_total.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(form, text="Registrar venta", command=self._vender).grid(row=4, column=0, columnspan=2, pady=10)

    def _cargar_variantes(self) -> None:
        nombre = self.v_venta_zapato.get()
        self._variantes = [e for e in self.negocio.inventario.get(nombre, []) if e.cantidad > 0]
        self.combo_variante["values"] = [f"Talla {e.talla} · {e.color} · {e.cantidad} disponibles" for e in self._variantes]
        self.v_venta_variante.set("")
        self._actualizar_total()

    def _variante_elegida(self) -> Optional[Existencia]:
        indice = self.combo_variante.current()
        if 0 <= indice < len(self._variantes):
            return self._variantes[indice]
        return None

    def _actualizar_total(self) -> None:
        existencia = self._variante_elegida()
        try:
            cantidad = int(self.v_venta_cantidad.get())
        except ValueError:
            cantidad = 0
        if existencia is None or cantidad < 1:
            self.lbl_total.config(text="Total: $0.00")
            return
        total = existencia.precio * cantidad * (1 - self.negocio.descuento / 100)
        extra = f"  (descuento {self.negocio.descuento:g}% aplicado)" if self.negocio.descuento else ""
        self.lbl_total.config(text=f"Total: {dinero(total)}{extra}")

    def _vender(self) -> None:
        existencia = self._variante_elegida()
        if existencia is None:
            messagebox.showinfo("Falta información", "Elija el zapato y su talla/color.")
            return
        try:
            cantidad = leer_cantidad(self.v_venta_cantidad.get())
            venta = self.negocio.vender(self.v_venta_zapato.get(), existencia, cantidad)
        except ValueError as error:
            messagebox.showwarning("No se pudo vender", str(error))
            return
        nombre = self.v_venta_zapato.get()
        self.v_venta_cantidad.set("1")
        self.refrescar()
        if nombre in self.negocio.inventario:  # conserva el zapato elegido
            self.v_venta_zapato.set(nombre)
            self._cargar_variantes()
        messagebox.showinfo("Venta registrada", f"Total: {dinero(venta.total)}")

    # ---------------- Reportes ----------------
    def _crear_reportes(self, pestañas: ttk.Notebook) -> None:
        tab = ttk.Frame(pestañas, padding=10)
        pestañas.add(tab, text="Reportes")
        self.tabla_ventas = crear_tabla(tab, [("zapato", "Zapato", 220), ("talla", "Talla", 70),
                                              ("color", "Color", 120), ("cantidad", "Cantidad", 80),
                                              ("descuento", "Descuento", 90), ("total", "Total", 110)], alto=16)
        self.lbl_ventas_totales = ttk.Label(tab, text="Ventas totales: $0.00", font=("TkDefaultFont", 13, "bold"))
        self.lbl_ventas_totales.pack(anchor="e", pady=(10, 0))

    # ---------------- Configuración ----------------
    def _crear_configuracion(self, pestañas: ttk.Notebook) -> None:
        tab = ttk.Frame(pestañas, padding=20)
        pestañas.add(tab, text="Configuración")
        form = ttk.LabelFrame(tab, text="Descuento", padding=14)
        form.pack(anchor="w")
        self.v_descuento = tk.StringVar(value="0")
        ttk.Label(form, text="Descuento (%)").grid(row=0, column=0, padx=6)
        ttk.Entry(form, textvariable=self.v_descuento, width=8).grid(row=0, column=1)
        ttk.Button(form, text="Guardar", command=self._guardar_descuento).grid(row=0, column=2, padx=10)
        self.lbl_descuento = ttk.Label(form, text="Descuento actual: 0%")
        self.lbl_descuento.grid(row=1, column=0, columnspan=3, pady=(8, 0), sticky="w")

    def _guardar_descuento(self) -> None:
        try:
            self.negocio.establecer_descuento(leer_precio(self.v_descuento.get()))
        except ValueError as error:
            messagebox.showwarning("Revise los datos", str(error))
            return
        self.lbl_descuento.config(text=f"Descuento actual: {self.negocio.descuento:g}%")
        self._actualizar_total()
        self._avisar_si_no_guardo()
        messagebox.showinfo("Listo", f"Descuento establecido en {self.negocio.descuento:g}%")

    # ---------------- Refresco ----------------
    def _avisar_si_no_guardo(self) -> None:
        if self.negocio.error_guardado:
            messagebox.showerror(
                "No se pudo guardar",
                f"El cambio se aplicó, pero no se pudo guardar en disco:\n{self.negocio.error_guardado}")
            self.negocio.error_guardado = None

    def refrescar(self) -> None:
        self._avisar_si_no_guardo()
        # Tabla de inventario
        self.tabla_inv.delete(*self.tabla_inv.get_children())
        self._filas.clear()
        for nombre, existencias in self.negocio.inventario.items():
            for e in existencias:
                iid = self.tabla_inv.insert("", "end", values=(nombre, e.talla, e.color, e.cantidad, dinero(e.precio)))
                self._filas[iid] = (nombre, e)

        # Combo de ventas
        nombres = [n for n, es in self.negocio.inventario.items() if any(e.cantidad > 0 for e in es)]
        self.combo_zapato["values"] = nombres
        if self.v_venta_zapato.get() not in nombres:
            self.v_venta_zapato.set("")
        self._cargar_variantes()

        # Reporte de ventas
        self.tabla_ventas.delete(*self.tabla_ventas.get_children())
        for v in self.negocio.ventas:
            self.tabla_ventas.insert("", "end", values=(v.zapato, v.talla, v.color, v.cantidad,
                                                        f"{v.descuento:g}%", dinero(v.total)))
        total = sum(v.total for v in self.negocio.ventas)
        self.lbl_ventas_totales.config(text=f"Ventas totales: {dinero(total)}")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
