# ============================================================
# ANALIZADOR LEXICO DEL MINI-C
# Es el lexer.c que vimos en clase pasado a Python.
# Recibe el codigo fuente y devuelve la lista de tokens con
# tipo, lexema, linea y columna, y la lista de errores lexicos.
#
# Uso solo del lexer (desde la carpeta raiz del proyecto):
#   python -m minic.lexer minic/ejemplos/valido.txt
#   python -m minic.lexer minic/ejemplos/error_lexico.txt
#
# ESPECIFICACION DE TOKENS (expresiones regulares)
# ------------------------------------------------------------
#   Tipo    Expresion regular              Ejemplos
#   RES     int | if | else | while        int, while
#   ID      [a-zA-Z_][a-zA-Z0-9_]*         x, total1, _aux
#   NUM     [0-9]+                         5, 120
#   OP      <= | >= | == | != | [+\-*/=<>] +, ==, <=
#   PAR     \( | \)                        ( )
#   LLAVE   \{ | \}                        { }
#   PYC     ;                              ;
#
# Se ignoran espacios, tabuladores y saltos de linea.
#
# ERRORES LEXICOS QUE SE DETECTAN
#   - Caracter no valido: cualquier caracter que no empieza
#     ningun token (ej: @ # $ ñ).
#   - Literal mal formado: un numero pegado a letras (ej: 12abc),
#     porque un identificador no puede empezar con digito.
# ============================================================

import sys

# Tipos de token (los mismos nombres que en compartido.h)
T_NUM = "NUM"
T_ID = "ID"
T_RES = "RES"
T_OP = "OP"
T_PAR = "PAR"
T_LLAVE = "LLAVE"
T_PYC = "PYC"

RESERVADAS = ["int", "if", "else", "while"]


class Token:
    def __init__(self, tipo, lex, linea, columna):
        self.tipo = tipo        # NUM, ID, RES, ...
        self.lex = lex          # el texto del token, ej: "x", "5", "while"
        self.linea = linea      # linea donde aparece (empieza en 1)
        self.columna = columna  # columna donde EMPIEZA el token (empieza en 1)

    def __repr__(self):
        return self.tipo + "(" + self.lex + ")"


def es_digito(c):
    return c >= "0" and c <= "9"


def es_letra(c):
    return (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or c == "_"


def posicion(linea, columna):
    """Texto de posicion para los mensajes de error."""
    return "(linea " + str(linea) + ", columna " + str(columna) + ")"


def analisis_lexico(entrada):
    """Recibe el texto y devuelve (lista de tokens, lista de errores lexicos)."""
    tokens = []
    errores = []
    i = 0          # posicion en el texto
    linea = 1      # linea actual
    columna = 1    # columna actual dentro de la linea

    while i < len(entrada):
        c = entrada[i]
        inicio = columna   # columna donde empieza lo que vamos a leer

        # 1. Salto de linea: sube la linea y la columna vuelve a 1
        if c == "\n":
            linea += 1
            columna = 1
            i += 1

        # 2. Espacios y tabuladores: se ignoran
        elif c == " " or c == "\t" or c == "\r":
            i += 1
            columna += 1

        # 3. NUMERO (o literal mal formado si le siguen letras)
        elif es_digito(c):
            num = ""
            while i < len(entrada) and es_digito(entrada[i]):
                num += entrada[i]
                i += 1
            if i < len(entrada) and es_letra(entrada[i]):
                # ej: 12abc -> se lee todo junto para reportarlo una sola vez
                while i < len(entrada) and (es_letra(entrada[i]) or es_digito(entrada[i])):
                    num += entrada[i]
                    i += 1
                errores.append("ERROR LEXICO " + posicion(linea, inicio) +
                               ": literal mal formado '" + num + "'")
            else:
                tokens.append(Token(T_NUM, num, linea, inicio))
            columna += len(num)

        # 4. IDENTIFICADOR o PALABRA RESERVADA
        elif es_letra(c):
            palabra = ""
            while i < len(entrada) and (es_letra(entrada[i]) or es_digito(entrada[i])):
                palabra += entrada[i]
                i += 1
            if palabra in RESERVADAS:
                tokens.append(Token(T_RES, palabra, linea, inicio))
            else:
                tokens.append(Token(T_ID, palabra, linea, inicio))
            columna += len(palabra)

        # 5. OPERADORES de dos caracteres: <= >= == !=
        elif entrada[i:i + 2] in ["<=", ">=", "==", "!="]:
            tokens.append(Token(T_OP, entrada[i:i + 2], linea, inicio))
            i += 2
            columna += 2

        # 6. OPERADORES de un caracter
        elif c in "+-*/=<>":
            tokens.append(Token(T_OP, c, linea, inicio))
            i += 1
            columna += 1

        # 7. PARENTESIS, LLAVES y PUNTO Y COMA
        elif c == "(" or c == ")":
            tokens.append(Token(T_PAR, c, linea, inicio))
            i += 1
            columna += 1
        elif c == "{" or c == "}":
            tokens.append(Token(T_LLAVE, c, linea, inicio))
            i += 1
            columna += 1
        elif c == ";":
            tokens.append(Token(T_PYC, c, linea, inicio))
            i += 1
            columna += 1

        # 8. ERROR LEXICO: caracter que no pertenece al lenguaje
        else:
            errores.append("ERROR LEXICO " + posicion(linea, inicio) +
                           ": caracter no valido '" + c + "'")
            i += 1
            columna += 1

    return tokens, errores


def imprimir_tokens(tokens, errores):
    """Muestra la tabla de tokens (tipo, lexema, linea, columna) y los errores."""
    print("TIPO    LEXEMA        LINEA  COLUMNA")
    print("------  ------------  -----  -------")
    for t in tokens:
        print(t.tipo.ljust(6), "", t.lex.ljust(12), "", str(t.linea).rjust(5), "", str(t.columna).rjust(7))
    if errores:
        print()
        for e in errores:
            print(e)
    print("\nTotal:", len(tokens), "token(s),", len(errores), "error(es) lexico(s).")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivo = open(sys.argv[1], "r", encoding="utf-8")
        codigo = archivo.read()
        archivo.close()
    else:
        codigo = input("Escribe el codigo a analizar: ")
    lista_tokens, lista_errores = analisis_lexico(codigo)
    imprimir_tokens(lista_tokens, lista_errores)
