# Representacion de entrada para el analizador semantico (Fase 1).
# Un programa mini-C se escribe a mano como una lista de sentencias.
#
# Expresiones:  ("num", 5) | ("var", "x") | ("op", "+", izq, der)
#   aritmeticos + - * /  dan int ;  comparaciones < > <= >= == !=  dan bool
# Sentencias:   ("decl", "int", "x", valor|None) | ("asig", "x", expr)
#               ("bloque", [...]) | ("if", cond, [si], [no]|None)
#               ("while", cond, [cuerpo])
#
# Tabla de simbolos propuesta para Alex:
#   tabla[nombre] = {"tipo": "int", "ambito": numero_de_ambito}


def num(valor):
    return ("num", valor)


def var(nombre):
    return ("var", nombre)


def op(operador, izquierda, derecha):
    return ("op", operador, izquierda, derecha)


def decl(tipo, nombre, valor=None):
    return ("decl", tipo, nombre, valor)


def asig(nombre, expr):
    return ("asig", nombre, expr)


def bloque(sentencias):
    return ("bloque", sentencias)


def sentencia_if(cond, bloque_si, bloque_no=None):
    return ("if", cond, bloque_si, bloque_no)


def sentencia_while(cond, cuerpo):
    return ("while", cond, cuerpo)


def _mostrar_expr(expr):
    etiqueta = expr[0]
    if etiqueta == "num":
        return str(expr[1])
    if etiqueta == "var":
        return expr[1]
    if etiqueta == "op":
        return "(" + _mostrar_expr(expr[2]) + " " + expr[1] + " " + \
               _mostrar_expr(expr[3]) + ")"
    return "?"


def mostrar(programa, nivel=0):
    """Imprime la lista de sentencias con sangria por cada ambito."""
    sangria = "   " * nivel
    for sentencia in programa:
        etiqueta = sentencia[0]
        if etiqueta == "decl":
            _, tipo, nombre, valor = sentencia
            texto = sangria + "decl " + tipo + " " + nombre
            if valor is not None:
                texto += " = " + _mostrar_expr(valor)
            print(texto)
        elif etiqueta == "asig":
            _, nombre, expr = sentencia
            print(sangria + "asig " + nombre + " = " + _mostrar_expr(expr))
        elif etiqueta == "bloque":
            print(sangria + "bloque {")
            mostrar(sentencia[1], nivel + 1)
            print(sangria + "}")
        elif etiqueta == "if":
            _, cond, bloque_si, bloque_no = sentencia
            print(sangria + "if " + _mostrar_expr(cond) + ":")
            mostrar(bloque_si, nivel + 1)
            if bloque_no is not None:
                print(sangria + "else:")
                mostrar(bloque_no, nivel + 1)
        elif etiqueta == "while":
            _, cond, cuerpo = sentencia
            print(sangria + "while " + _mostrar_expr(cond) + ":")
            mostrar(cuerpo, nivel + 1)


# Ejemplos para probar y para la demo del video.
# PROGRAMA_VALIDO equivale a:
#   int x = 5; int y; y = x + 3; if (y > 10) { int z = 1; y = y - z; }
PROGRAMA_VALIDO = [
    decl("int", "x", num(5)),
    decl("int", "y"),
    asig("y", op("+", var("x"), num(3))),
    sentencia_if(
        op(">", var("y"), num(10)),
        [
            decl("int", "z", num(1)),
            asig("y", op("-", var("y"), var("z"))),
        ],
    ),
]

# Usa 'w' sin declararla -> lo caza la revision de tipos y la de Alex.
PROGRAMA_VAR_NO_DECLARADA = [
    decl("int", "x", num(5)),
    asig("x", op("+", var("w"), num(1))),
]

# Declara 'x' dos veces -> lo caza la tabla de simbolos de Alex.
PROGRAMA_REDECLARACION = [
    decl("int", "x", num(5)),
    decl("int", "x", num(9)),
]

# Asigna un bool (resultado de 2 < 3) a un int -> error de tipos.
PROGRAMA_TIPO_INCOMPATIBLE = [
    decl("int", "x", num(0)),
    asig("x", op("<", num(2), num(3))),
]


if __name__ == "__main__":
    print("Representacion del PROGRAMA_VALIDO:")
    print("-" * 40)
    mostrar(PROGRAMA_VALIDO)
