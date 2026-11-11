# ============================================================
# ANALIZADOR LEXICO
# Es el lexer.c que vimos en clase pasado a Python, con algunos
# tokens extra que necesita el mini-C:  ;  { }  <=  >=  ==  !=
# ============================================================

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
    def __init__(self, tipo, lex, linea):
        self.tipo = tipo      # NUM, ID, RES, ...
        self.lex = lex        # el texto del token, ej: "x", "5", "while"
        self.linea = linea    # linea donde aparece (para los mensajes de error)

    def __repr__(self):
        return self.tipo + "(" + self.lex + ")"


def es_digito(c):
    return c >= "0" and c <= "9"


def es_letra(c):
    return (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or c == "_"


def analisis_lexico(entrada):
    """Recibe el texto y devuelve (lista de tokens, lista de errores lexicos)."""
    tokens = []
    errores = []
    i = 0
    linea = 1

    while i < len(entrada):
        c = entrada[i]

        # 1. Espacios y saltos de linea: se ignoran
        if c == "\n":
            linea += 1
            i += 1
        elif c == " " or c == "\t" or c == "\r":
            i += 1

        # 2. NUMERO
        elif es_digito(c):
            num = ""
            while i < len(entrada) and es_digito(entrada[i]):
                num += entrada[i]
                i += 1
            tokens.append(Token(T_NUM, num, linea))

        # 3. IDENTIFICADOR o PALABRA RESERVADA
        elif es_letra(c):
            palabra = ""
            while i < len(entrada) and (es_letra(entrada[i]) or es_digito(entrada[i])):
                palabra += entrada[i]
                i += 1
            if palabra in RESERVADAS:
                tokens.append(Token(T_RES, palabra, linea))
            else:
                tokens.append(Token(T_ID, palabra, linea))

        # 4. OPERADORES de dos caracteres: <= >= == !=
        elif entrada[i:i + 2] in ["<=", ">=", "==", "!="]:
            tokens.append(Token(T_OP, entrada[i:i + 2], linea))
            i += 2

        # 5. OPERADORES de un caracter
        elif c in "+-*/=<>":
            tokens.append(Token(T_OP, c, linea))
            i += 1

        # 6. PARENTESIS, LLAVES y PUNTO Y COMA
        elif c == "(" or c == ")":
            tokens.append(Token(T_PAR, c, linea))
            i += 1
        elif c == "{" or c == "}":
            tokens.append(Token(T_LLAVE, c, linea))
            i += 1
        elif c == ";":
            tokens.append(Token(T_PYC, c, linea))
            i += 1

        # 7. ERROR LEXICO: caracter que no pertenece al lenguaje
        else:
            errores.append("ERROR LEXICO (linea " + str(linea) + "): caracter no valido '" + c + "'")
            i += 1

    return tokens, errores
