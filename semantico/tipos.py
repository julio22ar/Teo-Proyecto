# Verificacion de compatibilidad de tipos (Fase 1).
# Tipos: int (numeros y + - * /) y bool (comparaciones < > <= >= == !=).
# Reglas: aritmeticos requieren int y dan int; comparaciones requieren int
# y dan bool; una asignacion/inicializacion debe coincidir en tipo; la
# condicion de if/while debe ser bool.
# Nota: la redeclaracion y la declaracion previa las revisa la tabla de
# simbolos de Alex; aqui solo se revisan los TIPOS.


class ErrorDeTipos(Exception):
    pass


ARITMETICOS = {"+", "-", "*", "/"}
COMPARACION = {"<", ">", "<=", ">=", "==", "!="}


# Ambitos: pila de diccionarios {nombre: tipo}; el ultimo es el bloque actual.
def _entrar_ambito(ambitos):
    ambitos.append({})


def _salir_ambito(ambitos):
    ambitos.pop()


def _declarar(ambitos, nombre, tipo):
    ambitos[-1][nombre] = tipo


def _buscar_tipo(ambitos, nombre):
    for ambito in reversed(ambitos):
        if nombre in ambito:
            return ambito[nombre]
    return None


def tipo_de_expresion(expr, ambitos):
    """Devuelve 'int' o 'bool', o lanza ErrorDeTipos."""
    etiqueta = expr[0]

    if etiqueta == "num":
        return "int"

    if etiqueta == "var":
        nombre = expr[1]
        tipo = _buscar_tipo(ambitos, nombre)
        if tipo is None:
            raise ErrorDeTipos(
                "No se puede determinar el tipo de '" + nombre +
                "': no esta declarada."
            )
        return tipo

    if etiqueta == "op":
        _, operador, izquierda, derecha = expr
        tipo_izq = tipo_de_expresion(izquierda, ambitos)
        tipo_der = tipo_de_expresion(derecha, ambitos)

        if operador in ARITMETICOS:
            if tipo_izq != "int" or tipo_der != "int":
                raise ErrorDeTipos(
                    "El operador '" + operador + "' necesita enteros, pero "
                    "recibio " + tipo_izq + " y " + tipo_der + "."
                )
            return "int"

        if operador in COMPARACION:
            if tipo_izq != "int" or tipo_der != "int":
                raise ErrorDeTipos(
                    "La comparacion '" + operador + "' necesita enteros, pero "
                    "recibio " + tipo_izq + " y " + tipo_der + "."
                )
            return "bool"

        raise ErrorDeTipos("Operador desconocido: '" + operador + "'.")

    raise ErrorDeTipos("Expresion con forma desconocida: " + str(expr))


def _verificar_bloque(sentencias, ambitos):
    for sentencia in sentencias:
        etiqueta = sentencia[0]

        if etiqueta == "decl":
            _, tipo, nombre, valor = sentencia
            if valor is not None:
                tipo_valor = tipo_de_expresion(valor, ambitos)
                if tipo_valor != tipo:
                    raise ErrorDeTipos(
                        "No se puede inicializar '" + nombre + "' (" + tipo +
                        ") con un valor de tipo " + tipo_valor + "."
                    )
            _declarar(ambitos, nombre, tipo)

        elif etiqueta == "asig":
            _, nombre, expr = sentencia
            tipo_var = _buscar_tipo(ambitos, nombre)
            if tipo_var is None:
                raise ErrorDeTipos(
                    "No se puede asignar: la variable '" + nombre +
                    "' no esta declarada."
                )
            tipo_expr = tipo_de_expresion(expr, ambitos)
            if tipo_expr != tipo_var:
                raise ErrorDeTipos(
                    "No se puede asignar un valor de tipo " + tipo_expr +
                    " a '" + nombre + "', que es de tipo " + tipo_var + "."
                )

        elif etiqueta == "bloque":
            _entrar_ambito(ambitos)
            _verificar_bloque(sentencia[1], ambitos)
            _salir_ambito(ambitos)

        elif etiqueta == "if":
            _, cond, bloque_si, bloque_no = sentencia
            tipo_cond = tipo_de_expresion(cond, ambitos)
            if tipo_cond != "bool":
                raise ErrorDeTipos(
                    "La condicion del 'if' debe ser una comparacion (bool), "
                    "no " + tipo_cond + "."
                )
            _entrar_ambito(ambitos)
            _verificar_bloque(bloque_si, ambitos)
            _salir_ambito(ambitos)
            if bloque_no is not None:
                _entrar_ambito(ambitos)
                _verificar_bloque(bloque_no, ambitos)
                _salir_ambito(ambitos)

        elif etiqueta == "while":
            _, cond, cuerpo = sentencia
            tipo_cond = tipo_de_expresion(cond, ambitos)
            if tipo_cond != "bool":
                raise ErrorDeTipos(
                    "La condicion del 'while' debe ser una comparacion (bool), "
                    "no " + tipo_cond + "."
                )
            _entrar_ambito(ambitos)
            _verificar_bloque(cuerpo, ambitos)
            _salir_ambito(ambitos)


def verificar_tipos(programa):
    """Recorre el programa y comprueba los tipos. Lanza ErrorDeTipos si falla."""
    ambitos = [{}]
    _verificar_bloque(programa, ambitos)


def analizar_tipos(programa):
    """Devuelve (correcto, mensaje) sin lanzar excepcion."""
    try:
        verificar_tipos(programa)
        return True, "Tipos correctos."
    except ErrorDeTipos as error:
        return False, str(error)


if __name__ == "__main__":
    from semantico.representacion import (
        PROGRAMA_VALIDO, PROGRAMA_VAR_NO_DECLARADA,
        PROGRAMA_REDECLARACION, PROGRAMA_TIPO_INCOMPATIBLE,
    )

    casos = [
        ("PROGRAMA_VALIDO", PROGRAMA_VALIDO),
        ("PROGRAMA_VAR_NO_DECLARADA", PROGRAMA_VAR_NO_DECLARADA),
        ("PROGRAMA_REDECLARACION", PROGRAMA_REDECLARACION),
        ("PROGRAMA_TIPO_INCOMPATIBLE", PROGRAMA_TIPO_INCOMPATIBLE),
    ]

    print("Verificacion de tipos sobre los programas de ejemplo:")
    print("-" * 56)
    for nombre, programa in casos:
        correcto, mensaje = analizar_tipos(programa)
        estado = "OK   " if correcto else "ERROR"
        print("[" + estado + "] " + nombre)
        print("         -> " + mensaje)
