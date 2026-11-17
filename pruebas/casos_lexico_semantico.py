"""Pruebas de la Fase 1 revisada: lexer y analizador semántico.

Ejecutar desde la raíz del repositorio:
    python pruebas/casos_lexico_semantico.py
    python pruebas/casos_lexico_semantico.py --solo-lexico
    python pruebas/casos_lexico_semantico.py --solo-tipos

El núcleo de Alex se conectará en semantico/analizador.py mediante
analizar_programa(programa) -> (correcto, mensaje). Mientras no exista,
sus casos se muestran como PENDIENTES y no se cuentan como aprobados.
"""

import argparse
import importlib.util
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from minic.lexer import analisis_lexico
from semantico.representacion import (
    asig, bloque, decl, num, op, sentencia_if, sentencia_while, var,
)
from semantico.tipos import analizar_tipos


def datos_tokens(tokens):
    return [(t.tipo, t.lex, t.linea, t.columna) for t in tokens]


def probar_lexer():
    """Comprueba tipo, lexema, línea, columna y errores concretos."""
    archivo_demo = RAIZ / "minic" / "ejemplos" / "error_lexico.txt"
    casos = [
        (
            "declaración correcta",
            "int x = 5;",
            [("RES", "int", 1, 1), ("ID", "x", 1, 5),
             ("OP", "=", 1, 7), ("NUM", "5", 1, 9),
             ("PYC", ";", 1, 10)],
            [],
        ),
        (
            "reservadas e identificadores",
            "if else while int _aux total1",
            [("RES", "if", 1, 1), ("RES", "else", 1, 4),
             ("RES", "while", 1, 9), ("RES", "int", 1, 15),
             ("ID", "_aux", 1, 19), ("ID", "total1", 1, 24)],
            [],
        ),
        (
            "línea y columna después de salto",
            "x = 1;\ny = 2;",
            [("ID", "x", 1, 1), ("OP", "=", 1, 3),
             ("NUM", "1", 1, 5), ("PYC", ";", 1, 6),
             ("ID", "y", 2, 1), ("OP", "=", 2, 3),
             ("NUM", "2", 2, 5), ("PYC", ";", 2, 6)],
            [],
        ),
        (
            "operadores de dos caracteres",
            "x<=10; y!=2;",
            [("ID", "x", 1, 1), ("OP", "<=", 1, 2),
             ("NUM", "10", 1, 4), ("PYC", ";", 1, 6),
             ("ID", "y", 1, 8), ("OP", "!=", 1, 9),
             ("NUM", "2", 1, 11), ("PYC", ";", 1, 12)],
            [],
        ),
        (
            "carácter inválido @",
            "x = 1 @ 2;",
            [("ID", "x", 1, 1), ("OP", "=", 1, 3),
             ("NUM", "1", 1, 5), ("NUM", "2", 1, 9),
             ("PYC", ";", 1, 10)],
            ["ERROR LEXICO (linea 1, columna 7): caracter no valido '@'"],
        ),
        (
            "dos caracteres inválidos",
            "x=#; y=$;",
            [("ID", "x", 1, 1), ("OP", "=", 1, 2),
             ("PYC", ";", 1, 4), ("ID", "y", 1, 6),
             ("OP", "=", 1, 7), ("PYC", ";", 1, 9)],
            ["ERROR LEXICO (linea 1, columna 3): caracter no valido '#'",
             "ERROR LEXICO (linea 1, columna 8): caracter no valido '$'"],
        ),
        (
            "literal mal formado",
            "int x = 12abc;",
            [("RES", "int", 1, 1), ("ID", "x", 1, 5),
             ("OP", "=", 1, 7), ("PYC", ";", 1, 14)],
            ["ERROR LEXICO (linea 1, columna 9): literal mal formado '12abc'"],
        ),
        (
            "archivo de demo error_lexico.txt",
            archivo_demo.read_text(encoding="utf-8"),
            None,  # Solo importan los tres errores de la demo.
            ["ERROR LEXICO (linea 2, columna 16): caracter no valido '@'",
             "ERROR LEXICO (linea 3, columna 17): caracter no valido '$'",
             "ERROR LEXICO (linea 4, columna 5): literal mal formado '3x'"],
        ),
    ]

    correctos = 0
    print("\nPRUEBAS DEL LEXER")
    for nombre, codigo, tokens_esperados, errores_esperados in casos:
        tokens, errores = analisis_lexico(codigo)
        tokens_obtenidos = datos_tokens(tokens)
        bien = errores == errores_esperados
        if tokens_esperados is not None:
            bien = bien and tokens_obtenidos == tokens_esperados
        print("[" + ("OK" if bien else "FALLO") + "] " + nombre)
        if not bien:
            print("    Tokens esperados:", tokens_esperados)
            print("    Tokens obtenidos:", tokens_obtenidos)
            print("    Errores esperados:", errores_esperados)
            print("    Errores obtenidos:", errores)
        correctos += bien
    return correctos, len(casos)


def casos_semanticos():
    """Misma representación de sentencias que usa el equipo en semantico/."""
    return [
        ("programa válido", [
            decl("int", "x", num(5)),
            decl("int", "y"),
            asig("y", op("+", var("x"), num(3))),
        ], True),
        ("x = y con y declarada", [
            decl("int", "x", num(5)),
            decl("int", "y", num(2)),
            asig("x", var("y")),
        ], True),
        ("x = y con y sin declarar", [
            decl("int", "x", num(5)),
            asig("x", var("y")),
        ], False),
        ("asignación a variable no declarada", [
            asig("x", num(1)),
        ], False),
        ("redeclaración en mismo ámbito", [
            decl("int", "x", num(1)),
            decl("int", "x", num(2)),
        ], False),
        ("sombreado en bloque interior", [
            decl("int", "x", num(1)),
            bloque([decl("int", "x", num(2))]),
            asig("x", num(3)),
        ], True),
        ("uso después de salir del ámbito", [
            bloque([decl("int", "x", num(1))]),
            asig("x", num(2)),
        ], False),
        ("uso de variable exterior en bloque", [
            decl("int", "x", num(1)),
            bloque([asig("x", num(2))]),
        ], True),
        ("tipo incompatible en asignación", [
            decl("int", "x", num(5)),
            asig("x", op("<", num(2), num(3))),
        ], False),
        ("tipo incompatible en inicialización", [
            decl("int", "x", op("<", num(2), num(3))),
        ], False),
        ("bool dentro de expresión aritmética", [
            decl("int", "x", op("+", op("<", num(2), num(3)), num(1))),
        ], False),
        ("condición de if no booleana", [
            sentencia_if(num(1), [decl("int", "x", num(2))]),
        ], False),
        ("condición de while válida", [
            decl("int", "x", num(1)),
            sentencia_while(op("<", var("x"), num(3)), [asig("x", num(2))]),
        ], True),
    ]


def probar_semantico(analizador, titulo, casos):
    correctos = 0
    print("\n" + titulo)
    for nombre, programa, esperado in casos:
        try:
            resultado = analizador(programa)
            if (not isinstance(resultado, tuple) or len(resultado) != 2 or
                    not isinstance(resultado[0], bool)):
                raise ValueError("La función debe devolver (bool, mensaje).")
            correcto, mensaje = resultado
            bien = correcto == esperado and (correcto or bool(mensaje))
        except Exception as error:
            bien = False
            mensaje = "Excepción inesperada: " + repr(error)
        print("[" + ("OK" if bien else "FALLO") + "] " + nombre)
        if not bien:
            print("    Esperado:", esperado, "| Obtenido:", mensaje)
        correctos += bien
    return correctos, len(casos)


def main():
    opciones = argparse.ArgumentParser(description=__doc__)
    opciones.add_argument("--solo-lexico", action="store_true")
    opciones.add_argument("--solo-tipos", action="store_true")
    args = opciones.parse_args()
    if args.solo_lexico and args.solo_tipos:
        opciones.error("Seleccione solo una de las dos opciones.")

    aprobadas = ejecutadas = pendientes = 0
    if not args.solo_tipos:
        bien, total = probar_lexer()
        aprobadas += bien
        ejecutadas += total

    if not args.solo_lexico:
        # El módulo de tipos existe; la tabla de símbolos aún es de Alex.
        tipos = [caso for caso in casos_semanticos()
                 if caso[0] not in {
                     "redeclaración en mismo ámbito",
                     "sombreado en bloque interior",
                 }]
        bien, total = probar_semantico(analizar_tipos, "PRUEBAS DE TIPOS Y USO DE VARIABLES", tipos)
        aprobadas += bien
        ejecutadas += total

        if not args.solo_tipos:
            modulo = "semantico.analizador"
            if importlib.util.find_spec(modulo) is None:
                pendientes = len(casos_semanticos())
                print("\nPRUEBAS DEL NÚCLEO SEMÁNTICO: PENDIENTES (" +
                      str(pendientes) + ")")
                print("Falta semantico/analizador.py con "
                      "analizar_programa(programa) -> (bool, mensaje).")
            else:
                from semantico.analizador import analizar_programa
                bien, total = probar_semantico(
                    analizar_programa, "PRUEBAS DEL NÚCLEO SEMÁNTICO", casos_semanticos()
                )
                aprobadas += bien
                ejecutadas += total

    print("\nRESUMEN: " + str(aprobadas) + "/" + str(ejecutadas) +
          " ejecutadas correctas; " + str(pendientes) + " pendientes.")
    if aprobadas != ejecutadas:
        return 1
    if pendientes:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
