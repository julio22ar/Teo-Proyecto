# ============================================================
# PARSER DESCENDENTE RECURSIVO PARA EL MINI-C
# Hay una funcion por cada no terminal de gramatica.txt.
# Cada funcion consume sus tokens y devuelve su Nodo del arbol.
# Si algo no cuadra con la gramatica se lanza ErrorSintactico.
# ============================================================

from arbol import Nodo
from minic.lexer import T_NUM, T_ID

COMPARADORES = ["<", ">", "<=", ">=", "==", "!="]


class ErrorSintactico(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0          # posicion del token que estamos viendo

    # ---------- FUNCIONES AUXILIARES ----------

    def actual(self):
        """Devuelve el token actual, o None si ya no hay mas."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def ve(self, lex):
        """True si el token actual tiene ese texto (ej: ve("if"))."""
        t = self.actual()
        return t is not None and t.lex == lex and t.tipo not in (T_NUM, T_ID)

    def ve_tipo(self, tipo):
        """True si el token actual es de ese tipo (ej: ve_tipo(T_ID))."""
        t = self.actual()
        return t is not None and t.tipo == tipo

    def error(self, esperado):
        t = self.actual()
        if t is None:
            ultima = self.tokens[-1].linea if self.tokens else 1
            raise ErrorSintactico("ERROR SINTACTICO (linea " + str(ultima) + "): se esperaba "
                                  + esperado + " pero se acabo la entrada")
        raise ErrorSintactico("ERROR SINTACTICO (linea " + str(t.linea) + "): se esperaba "
                              + esperado + " pero se encontro '" + t.lex + "'")

    def consumir(self, lex):
        """Revisa que el token actual sea 'lex', avanza y devuelve la hoja."""
        if not self.ve(lex):
            self.error("'" + lex + "'")
        self.pos += 1
        return Nodo(lex)

    def consumir_tipo(self, tipo, nombre):
        """Igual que consumir pero para NUM e ID (importa el tipo, no el texto)."""
        if not self.ve_tipo(tipo):
            self.error(nombre)
        t = self.actual()
        self.pos += 1
        return Nodo(tipo + ": " + t.lex)

    # ---------- REGLAS DE LA GRAMATICA ----------

    # <programa> ::= <instrucciones>
    def programa(self):
        nodo = Nodo("programa")
        nodo.agregar(self.instrucciones())
        if self.actual() is not None:      # sobro algo, ej: una '}' de mas
            self.error("una instruccion")
        return nodo

    # <instrucciones> ::= { <instruccion> }
    def instrucciones(self):
        nodo = Nodo("instrucciones")
        # se repite hasta que se acabe la entrada o se cierre el bloque
        while self.actual() is not None and not self.ve("}"):
            nodo.agregar(self.instruccion())
        return nodo

    # <instruccion> ::= <declaracion> | <asignacion> | <condicional> | <ciclo>
    def instruccion(self):
        nodo = Nodo("instruccion")
        if self.ve("int"):
            nodo.agregar(self.declaracion())
        elif self.ve_tipo(T_ID):
            nodo.agregar(self.asignacion())
        elif self.ve("if"):
            nodo.agregar(self.condicional())
        elif self.ve("while"):
            nodo.agregar(self.ciclo())
        else:
            self.error("una instruccion (int, identificador, if o while)")
        return nodo

    # <declaracion> ::= "int" ID [ "=" <expresion> ] ";"
    def declaracion(self):
        nodo = Nodo("declaracion")
        nodo.agregar(self.consumir("int"))
        nodo.agregar(self.consumir_tipo(T_ID, "un identificador"))
        if self.ve("="):
            nodo.agregar(self.consumir("="))
            nodo.agregar(self.expresion())
        nodo.agregar(self.consumir(";"))
        return nodo

    # <asignacion> ::= ID "=" <expresion> ";"
    def asignacion(self):
        nodo = Nodo("asignacion")
        nodo.agregar(self.consumir_tipo(T_ID, "un identificador"))
        nodo.agregar(self.consumir("="))
        nodo.agregar(self.expresion())
        nodo.agregar(self.consumir(";"))
        return nodo

    # <condicional> ::= "if" "(" <condicion> ")" <bloque> [ "else" <bloque> ]
    def condicional(self):
        nodo = Nodo("condicional")
        nodo.agregar(self.consumir("if"))
        nodo.agregar(self.consumir("("))
        nodo.agregar(self.condicion())
        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.bloque())
        if self.ve("else"):
            nodo.agregar(self.consumir("else"))
            nodo.agregar(self.bloque())
        return nodo

    # <ciclo> ::= "while" "(" <condicion> ")" <bloque>
    def ciclo(self):
        nodo = Nodo("ciclo")
        nodo.agregar(self.consumir("while"))
        nodo.agregar(self.consumir("("))
        nodo.agregar(self.condicion())
        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.bloque())
        return nodo

    # <bloque> ::= "{" <instrucciones> "}"
    def bloque(self):
        nodo = Nodo("bloque")
        nodo.agregar(self.consumir("{"))
        nodo.agregar(self.instrucciones())
        nodo.agregar(self.consumir("}"))
        return nodo

    # <condicion> ::= <expresion> <comparador> <expresion>
    def condicion(self):
        nodo = Nodo("condicion")
        nodo.agregar(self.expresion())
        nodo.agregar(self.comparador())
        nodo.agregar(self.expresion())
        return nodo

    # <comparador> ::= "<" | ">" | "<=" | ">=" | "==" | "!="
    def comparador(self):
        nodo = Nodo("comparador")
        for comp in COMPARADORES:
            if self.ve(comp):
                nodo.agregar(self.consumir(comp))
                return nodo
        self.error("un comparador (<, >, <=, >=, ==, !=)")

    # <expresion> ::= <termino> { ("+" | "-") <termino> }
    def expresion(self):
        nodo = Nodo("expresion")
        nodo.agregar(self.termino())
        while self.ve("+") or self.ve("-"):
            nodo.agregar(self.consumir(self.actual().lex))
            nodo.agregar(self.termino())
        return nodo

    # <termino> ::= <factor> { ("*" | "/") <factor> }
    def termino(self):
        nodo = Nodo("termino")
        nodo.agregar(self.factor())
        while self.ve("*") or self.ve("/"):
            nodo.agregar(self.consumir(self.actual().lex))
            nodo.agregar(self.factor())
        return nodo

    # <factor> ::= NUM | ID | "(" <expresion> ")"
    def factor(self):
        nodo = Nodo("factor")
        if self.ve_tipo(T_NUM):
            nodo.agregar(self.consumir_tipo(T_NUM, "un numero"))
        elif self.ve_tipo(T_ID):
            nodo.agregar(self.consumir_tipo(T_ID, "un identificador"))
        elif self.ve("("):
            nodo.agregar(self.consumir("("))
            nodo.agregar(self.expresion())
            nodo.agregar(self.consumir(")"))
        else:
            self.error("un numero, un identificador o '('")
        return nodo


def analizar(tokens):
    """Funcion que usan los demas: recibe tokens y devuelve el arbol."""
    return Parser(tokens).programa()
