# ============================================================
# PARSER DESCENDENTE RECURSIVO PARA EL ESPANOL REDUCIDO
# Una funcion por no terminal de gramatica_es.txt.
# Devuelve el mismo tipo de arbol que el parser del mini-C.
# ============================================================

import re

from arbol import Nodo
from espanol.vocabulario import (
    ADJETIVOS, ADVERBIOS, DETERMINANTES, PREPOSICIONES,
    SUSTANTIVOS, VERBOS,
)


class ErrorSintacticoEspanol(Exception):
    pass


class ParserEspanol:
    def __init__(self, oracion):
        # Conservamos la palabra original para mostrarla en el arbol.
        self.tokens = re.findall(r"\w+|[^\w\s]", oracion, re.UNICODE)
        self.pos = 0

    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].lower()
        return None

    def error(self, esperado):
        palabra = self.actual()
        if palabra is None:
            raise ErrorSintacticoEspanol(
                "Se esperaba " + esperado + " pero terminó la oración."
            )
        raise ErrorSintacticoEspanol(
            "Se esperaba " + esperado + " pero se encontró '" +
            self.tokens[self.pos] + "' (palabra " + str(self.pos + 1) + ")."
        )

    def consumir(self, categoria, palabras):
        palabra = self.actual()
        if palabra not in palabras:
            self.error("un " + categoria)
        original = self.tokens[self.pos]
        self.pos += 1
        return Nodo(categoria.upper() + ": " + original), palabra

    def comprobar_concordancia(self, palabra, rasgos, genero, numero):
        if rasgos != (genero, numero):
            raise ErrorSintacticoEspanol(
                "Error de concordancia de género o número en '" + palabra +
                "': se esperaba " + genero + " " + numero + "."
            )

    # <oracion> ::= [ <adverbio> ] <sujeto> <predicado> [ "." ]
    def oracion(self):
        nodo = Nodo("oracion")
        if self.actual() in ADVERBIOS:
            nodo.agregar(self.adverbio())
        sujeto, numero = self.sujeto()
        nodo.agregar(sujeto)
        nodo.agregar(self.predicado(numero))
        if self.actual() == ".":
            nodo.agregar(Nodo("."))
            self.pos += 1
        if self.actual() is not None:
            self.error("el final de la oración")
        return nodo

    # <sujeto> ::= <grupo_nominal>
    def sujeto(self):
        nodo = Nodo("sujeto")
        grupo, numero = self.grupo_nominal()
        nodo.agregar(grupo)
        return nodo, numero

    # <predicado> ::= [ <adverbio> ] <verbo> [ <adverbio> ]
    #                 <objeto> [ <adverbio> ]
    def predicado(self, numero_sujeto):
        nodo = Nodo("predicado")
        if self.actual() in ADVERBIOS:
            nodo.agregar(self.adverbio())
        hoja, verbo = self.consumir("verbo", VERBOS)
        if VERBOS[verbo][1] != numero_sujeto:
            raise ErrorSintacticoEspanol(
                "Error de concordancia sujeto-verbo en '" + verbo +
                "': se esperaba número " + numero_sujeto + "."
            )
        verbo_nodo = Nodo("verbo")
        verbo_nodo.agregar(hoja)
        nodo.agregar(verbo_nodo)
        if self.actual() in ADVERBIOS:
            nodo.agregar(self.adverbio())
        nodo.agregar(self.objeto())
        if self.actual() in ADVERBIOS:
            nodo.agregar(self.adverbio())
        return nodo

    # <objeto> ::= [ "a" ] <grupo_nominal>
    def objeto(self):
        nodo = Nodo("objeto")
        if self.actual() == "a":
            nodo.agregar(Nodo("a"))
            self.pos += 1
        grupo, _ = self.grupo_nominal()
        nodo.agregar(grupo)
        return nodo

    # <grupo_nominal> ::= <determinante> [ <adjetivo> ] <sustantivo>
    #                     [ <adjetivo> ] [ <frase_preposicional> ]
    def grupo_nominal(self):
        nodo = Nodo("grupo_nominal")
        hoja, determinante = self.consumir("determinante", DETERMINANTES)
        genero, numero = DETERMINANTES[determinante]
        det_nodo = Nodo("determinante")
        det_nodo.agregar(hoja)
        nodo.agregar(det_nodo)
        if self.actual() in ADJETIVOS:
            nodo.agregar(self.adjetivo(genero, numero))
        hoja, sustantivo = self.consumir("sustantivo", SUSTANTIVOS)
        self.comprobar_concordancia(sustantivo, SUSTANTIVOS[sustantivo], genero, numero)
        sust_nodo = Nodo("sustantivo")
        sust_nodo.agregar(hoja)
        nodo.agregar(sust_nodo)
        if self.actual() in ADJETIVOS:
            nodo.agregar(self.adjetivo(genero, numero))
        if self.actual() in PREPOSICIONES:
            nodo.agregar(self.frase_preposicional())
        return nodo, numero

    def adjetivo(self, genero, numero):
        nodo = Nodo("adjetivo")
        hoja, palabra = self.consumir("adjetivo", ADJETIVOS)
        self.comprobar_concordancia(palabra, ADJETIVOS[palabra], genero, numero)
        nodo.agregar(hoja)
        return nodo

    def adverbio(self):
        nodo = Nodo("adverbio")
        hoja, _ = self.consumir("adverbio", ADVERBIOS)
        nodo.agregar(hoja)
        return nodo

    # <frase_preposicional> ::= <preposicion> <grupo_nominal>
    def frase_preposicional(self):
        nodo = Nodo("frase_preposicional")
        prep_nodo = Nodo("preposicion")
        hoja, _ = self.consumir("preposicion", PREPOSICIONES)
        prep_nodo.agregar(hoja)
        nodo.agregar(prep_nodo)
        grupo, _ = self.grupo_nominal()
        nodo.agregar(grupo)
        return nodo


def analizar_oracion(oracion):
    """Devuelve (aceptada, arbol, mensaje_error) para una oración."""
    try:
        arbol = ParserEspanol(oracion).oracion()
        return True, arbol, None
    except ErrorSintacticoEspanol as error:
        return False, None, str(error)
