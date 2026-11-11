# ============================================================
# ARBOL DE ANALISIS SINTACTICO
# Cada nodo tiene una etiqueta y una lista de hijos.
#   - Nodo interno: un no terminal de la gramatica (ej: "expresion")
#   - Hoja: un token (ej: "ID: x", "NUM: 5", ";")
# Esta misma clase se puede reutilizar en la Fase 2 para el espanol.
# ============================================================


class Nodo:
    def __init__(self, etiqueta):
        self.etiqueta = etiqueta
        self.hijos = []

    def agregar(self, hijo):
        self.hijos.append(hijo)


def imprimir_arbol(nodo, nivel=0):
    """Imprime el arbol en la consola usando sangria para cada nivel."""
    print("   " * nivel + "|- " + nodo.etiqueta)
    for hijo in nodo.hijos:
        imprimir_arbol(hijo, nivel + 1)
