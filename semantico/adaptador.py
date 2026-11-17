"""Convierte el árbol mini-C a la representación del verificador semántico.

Reutiliza la sintaxis reconocida por minic.parser; no ejecuta el código fuente.
"""

from semantico.representacion import asig, decl, num, op, sentencia_if, sentencia_while, var


def _identificador(hoja):
    return hoja.etiqueta.removeprefix("ID: ")


def _expresion(nodo):
    if nodo.etiqueta in ("expresion", "termino"):
        # El parser mantiene cada nivel de precedencia en una lista. Se pliega
        # a la izquierda para conservar la asociatividad de resta y división.
        resultado = _expresion(nodo.hijos[0])
        for indice in range(1, len(nodo.hijos), 2):
            resultado = op(nodo.hijos[indice].etiqueta, resultado,
                           _expresion(nodo.hijos[indice + 1]))
        return resultado
    if nodo.etiqueta == "factor":
        hoja = nodo.hijos[0]
        if hoja.etiqueta.startswith("NUM: "):
            return num(int(hoja.etiqueta.removeprefix("NUM: ")))
        if hoja.etiqueta.startswith("ID: "):
            return var(_identificador(hoja))
        if hoja.etiqueta == "(":
            return _expresion(nodo.hijos[1])
    raise ValueError("Expresión no reconocida en el árbol mini-C: " + nodo.etiqueta)


def _condicion(nodo):
    izquierda, comparador, derecha = nodo.hijos
    return op(comparador.hijos[0].etiqueta,
              _expresion(izquierda), _expresion(derecha))


def _bloque(nodo):
    return _instrucciones(nodo.hijos[1])


def _instruccion(nodo):
    if nodo.etiqueta == "declaracion":
        valor = _expresion(nodo.hijos[3]) if len(nodo.hijos) == 5 else None
        return decl(nodo.hijos[0].etiqueta, _identificador(nodo.hijos[1]), valor)
    if nodo.etiqueta == "asignacion":
        return asig(_identificador(nodo.hijos[0]), _expresion(nodo.hijos[2]))
    if nodo.etiqueta == "condicional":
        alternativa = _bloque(nodo.hijos[6]) if len(nodo.hijos) == 7 else None
        return sentencia_if(_condicion(nodo.hijos[2]), _bloque(nodo.hijos[4]), alternativa)
    if nodo.etiqueta == "ciclo":
        return sentencia_while(_condicion(nodo.hijos[2]), _bloque(nodo.hijos[4]))
    raise ValueError("Instrucción no reconocida en el árbol mini-C: " + nodo.etiqueta)


def _instrucciones(nodo):
    return [_instruccion(hijo.hijos[0]) for hijo in nodo.hijos]


def programa_desde_arbol(arbol):
    """Devuelve las tuplas que consumen analizar_tipos y analizar_programa."""
    if arbol.etiqueta != "programa":
        raise ValueError("Se esperaba la raíz de un programa mini-C.")
    return _instrucciones(arbol.hijos[0])
