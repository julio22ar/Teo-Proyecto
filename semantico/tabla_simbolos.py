class ErrorSemantico(Exception):
    pass


class TablaSimbolos:
    def __init__(self):
        self.ambitos = [{}]     

    def nivel(self):
        """Numero del ambito actual (0 = global)."""
        return len(self.ambitos) - 1

    def entrar_ambito(self):
        """Se llama al abrir un bloque { }."""
        self.ambitos.append({})

    def salir_ambito(self):
        """Se llama al cerrar el bloque: se borran sus variables."""
        self.ambitos.pop()

    def declarar(self, nombre, tipo):
        """Anota una variable nueva en el ambito actual.
        Error si ya estaba declarada EN ESTE MISMO ambito (redeclaracion)."""
        actual = self.ambitos[-1]
        if nombre in actual:
            raise ErrorSemantico(
                "Redeclaracion: la variable '" + nombre + "' ya fue declarada "
                "en este mismo ambito (ambito " + str(self.nivel()) + ")."
            )
        actual[nombre] = {"tipo": tipo, "ambito": self.nivel()}

    def buscar(self, nombre):
        """Devuelve la entrada {"tipo", "ambito"} de la variable visible
        mas cercana, o None si no esta declarada en ningun ambito."""
        for tabla in reversed(self.ambitos):
            if nombre in tabla:
                return tabla[nombre]
        return None

    def mostrar(self):
        """Imprime el contenido actual de la tabla (para la demo)."""
        for numero, tabla in enumerate(self.ambitos):
            if tabla:
                variables = ", ".join(
                    nombre + ":" + datos["tipo"] for nombre, datos in tabla.items()
                )
            else:
                variables = "(vacio)"
            print("      ambito " + str(numero) + " -> " + variables)
