# ============================================================
# PROGRAMA PRINCIPAL
# Uso:
#   python main.py minic/ejemplos/valido.txt    -> analiza un archivo
#   python main.py                         -> pide una linea por teclado
# ============================================================

import sys
from minic.lexer import analisis_lexico
from minic.parser import analizar, ErrorSintactico
from arbol import imprimir_arbol


def procesar(entrada):
    """Corre lexer + parser. Devuelve True si la entrada es valida."""
    print("--- ANALISIS LEXICO ---")
    tokens, errores = analisis_lexico(entrada)
    for t in tokens:
        print(t.tipo.ljust(6), ":", t.lex)
    for e in errores:
        print(e)
    if len(errores) > 0:
        print("\nHay errores lexicos, no se hace el analisis sintactico.")
        return False

    print("\n--- ANALISIS SINTACTICO ---")
    try:
        arbol = analizar(tokens)
    except ErrorSintactico as e:
        print(e)
        print("Entrada RECHAZADA.")
        return False

    imprimir_arbol(arbol)
    print("\nEntrada ACEPTADA: pertenece al lenguaje.")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivo = open(sys.argv[1], "r")
        entrada = archivo.read()
        archivo.close()
    else:
        entrada = input("Escribe el codigo a analizar: ")
    procesar(entrada)
