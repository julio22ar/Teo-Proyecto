import io
import os
import sys
from contextlib import redirect_stdout


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import procesar


VALIDOS = [
    ("declaracion simple",            "int x;"),
    ("declaracion con valor",         "int x = 5;"),
    ("asignacion con suma",           "x = y + 3;"),
    ("precedencia de operadores",     "x = 2 + 3 * 4 - 6 / 2;"),
    ("expresion con parentesis",      "x = (a + b) * (c - 1);"),
    ("parentesis anidados",           "x = ((1 + 2) * 3);"),
    ("if sin else",                   "if (x > 0) { x = x - 1; }"),
    ("if con else",                   "if (x == 0) { y = 1; } else { y = 2; }"),
    ("while",                         "while (i < 10) { i = i + 1; }"),
    ("while con if adentro",          "while (i <= 10) { if (i != 5) { s = s + i; } i = i + 1; }"),
    ("bloque vacio",                  "if (a >= b) { }"),
    ("varias instrucciones",          "int a = 1;\nint b = 2;\nint c;\nc = a + b;"),
]


INVALIDOS = [
    ("falta punto y coma",            "int x = 5"),
    ("falta operando",                "x = 5 + ;"),
    ("dos numeros sin operador",      "x = 5 3;"),
    ("dos operadores seguidos",       "x = 5 + * 3;"),
    ("parentesis sin cerrar",         "x = (1 + 2;"),
    ("parentesis de mas",             "x = 1 + 2);"),
    ("numero en lugar de variable",   "int 5;"),
    ("asignar a un numero",           "5 = x;"),
    ("condicion sin comparador",      "if (x) { y = 1; }"),
    ("if sin llaves",                 "if (x > 0) y = 1;"),
    ("llave sin cerrar",              "while (x < 3) { x = x + 1;"),
    ("else sin if",                   "else { x = 1; }"),
    ("caracter no valido (lexico)",   "x = 4 @ 2;"),
]


def probar(casos, esperado):
    """Corre una lista de casos y devuelve cuantos dieron el resultado esperado."""
    correctos = 0
    for descripcion, codigo in casos:
    
        with redirect_stdout(io.StringIO()):
            resultado = procesar(codigo)

        if resultado == esperado:
            estado = "OK   "
            correctos += 1
        else:
            estado = "FALLO"
        print(" ", estado, "|", descripcion.ljust(30), "|", codigo.replace("\n", " "))
    return correctos


if __name__ == "__main__":
    print("ENTRADAS VALIDAS (el parser debe aceptarlas)")
    ok_validos = probar(VALIDOS, True)

    print("\nENTRADAS INVALIDAS (el parser debe rechazarlas)")
    ok_invalidos = probar(INVALIDOS, False)

    total = len(VALIDOS) + len(INVALIDOS)
    print("\nRESUMEN")
    print("  Validas aceptadas   :", ok_validos, "de", len(VALIDOS))
    print("  Invalidas rechazadas:", ok_invalidos, "de", len(INVALIDOS))
    print("  Total correctas     :", ok_validos + ok_invalidos, "de", total)