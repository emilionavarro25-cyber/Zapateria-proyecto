class Zapateria:
    def __init__(self):
        self.inventario = {}
        self.ventas = []
        self.configuraciones = {"descuento": 0.0}

    def menu_principal(self):
        opciones = {
            "1": self.gestion_inventario,
            "2": self.registrar_ventas,
            "3": self.mostrar_reportes,
            "4": self.configuraciones_usuario,
            "5": self.salir
        }
        while True:
            print("\n*** Bienvenido al Sistema de Gestión de Zapaterías Rija ***")
            print("1. Gestión de Inventario\n2. Registro de Ventas\n3. Reportes\n4. Configuraciones\n5. Salir")
            opcion = input("Seleccione una opción: ")
            accion = opciones.get(opcion)
            if accion:
                accion()
            else:
                print("Opción no válida.")

    def salir(self):
        print("Gracias por usar el sistema de Zapaterías Rija. ¡Hasta luego!")
        exit()

    def gestion_inventario(self):
        opciones = {
            "1": self.agregar_zapato,
            "2": self.modificar_zapato,
            "3": self.consultar_inventario,
            "4": lambda: None
        }
        while True:
            print("\n--- Gestión de Inventario ---")
            print("1. Agregar Zapato\n2. Modificar Zapato\n3. Consultar Inventario\n4. Volver al Menú Principal")
            opcion = input("Seleccione una opción: ")
            if opcion == "4":
                break
            accion = opciones.get(opcion)
            if accion:
                accion()
            else:
                print("Opción no válida.")

    def agregar_zapato(self):
        nombre = input("Nombre del zapato: ")
        color = input("Color: ")
        precio = float(input("Precio: "))
        tallas = input("Tallas y cantidades (ej. 'Talla 39: 10, Talla 40: 15'): ")

        try:
            for talla_info in tallas.split(","):
                talla, cantidad = talla_info.split(":")
                talla, cantidad = talla.strip(), int(cantidad.strip())
                self.inventario.setdefault(nombre, []).append({"talla": talla, "color": color, "cantidad": cantidad, "precio": precio})
            print(f"Zapato {nombre} agregado al inventario.")
        except ValueError:
            print("Formato incorrecto.")

    def modificar_zapato(self):
        nombre = input("Nombre del zapato a modificar: ")
        if nombre in self.inventario:
            self.listar_zapatos(nombre)
            indice = int(input("Seleccione un zapato: ")) - 1
            if 0 <= indice < len(self.inventario[nombre]):
                self.modificar_dato_zapato(nombre, indice)
            else:
                print("Índice no válido.")
        else:
            print("Zapato no encontrado.")

    def listar_zapatos(self, nombre):
        for i, zapato in enumerate(self.inventario[nombre]):
            print(f"{i + 1}. Talla: {zapato['talla']}, Color: {zapato['color']}, Cantidad: {zapato['cantidad']}, Precio: {zapato['precio']}")

    def modificar_dato_zapato(self, nombre, indice):
        opciones = {
            "1": lambda: self.modificar_atributo(nombre, indice, "talla"),
            "2": lambda: self.modificar_atributo(nombre, indice, "color"),
            "3": lambda: self.modificar_atributo(nombre, indice, "cantidad"),
            "4": lambda: self.modificar_atributo(nombre, indice, "precio")
        }
        print("1. Talla\n2. Color\n3. Cantidad\n4. Precio")
        opcion = input("Seleccione qué modificar: ")
        accion = opciones.get(opcion)
        if accion:
            accion()
        else:
            print("Opción no válida.")

    def modificar_atributo(self, nombre, indice, atributo):
        nuevo_valor = input(f"Nuevo {atributo}: ")
        if atributo in ["cantidad", "precio"]:
            nuevo_valor = int(nuevo_valor) if atributo == "cantidad" else float(nuevo_valor)
        self.inventario[nombre][indice][atributo] = nuevo_valor

    def consultar_inventario(self):
        if not self.inventario:
            print("El inventario está vacío.")
        else:
            for nombre, zapatos in self.inventario.items():
                for zapato in zapatos:
                    print(f"{nombre}, Talla: {zapato['talla']}, Color: {zapato['color']}, Cantidad: {zapato['cantidad']}, Precio: {zapato['precio']}")

    def registrar_ventas(self):
        nombre = input("Nombre del zapato vendido: ")
        if nombre in self.inventario:
            talla = input("Talla del zapato vendido: ")
            color = input("Color del zapato vendido: ")
            cantidad = int(input("Cantidad vendida: "))
            if self.realizar_venta(nombre, talla, color, cantidad):
                print(f"Venta registrada.")
            else:
                print("No hay suficiente inventario.")
        else:
            print("Zapato no encontrado.")

    def realizar_venta(self, nombre, talla, color, cantidad):
        for zapato in self.inventario[nombre]:
            if zapato['talla'] == talla and zapato['color'] == color and zapato['cantidad'] >= cantidad:
                zapato['cantidad'] -= cantidad
                total = zapato['precio'] * cantidad
                self.ventas.append({"zapato": nombre, "talla": talla, "color": color, "cantidad": cantidad, "total": total})
                return True
        return False

    def mostrar_reportes(self):
        if not self.ventas:
            print("No se han registrado ventas.")
        else:
            total_ventas = sum(venta["total"] for venta in self.ventas)
            print(f"Ventas Totales: ${total_ventas}")
            for venta in self.ventas:
                print(f"Venta: {venta['cantidad']} {venta['zapato']}(s), Talla: {venta['talla']}, Color: {venta['color']}, Total: ${venta['total']}")

    def configuraciones_usuario(self):
        print("1. Establecer Descuento\n2. Volver al Menú Principal")
        opcion = input("Seleccione una opción: ")
        if opcion == "1":
            descuento = float(input("Ingrese el descuento (%): "))
            self.configuraciones["descuento"] = descuento
            print(f"Descuento establecido en {descuento}%")
        elif opcion == "2":
            return
        else:
            print("Opción no válida.")

zapateria = Zapateria()
zapateria.menu_principal()
