import csv
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from arbol import Nodo, imprimir_arbol
from minic.lexer import analisis_lexico
from minic.parser import analizar, ErrorSintactico
from espanol.vocabulario import (
    DETERMINANTES, SUSTANTIVOS, ADJETIVOS, VERBOS, ADVERBIOS, PREPOSICIONES,
)


class ErrorIngenuo(Exception):
    pass


class ParserIngenuo:
    def __init__(self, oracion):
        self.palabras = oracion.lower().replace(".", "").split()
        self.pos = 0

    def actual(self):
        if self.pos < len(self.palabras):
            return self.palabras[self.pos]
        return None

    def consumir(self, categoria, lista):
        palabra = self.actual()
        if palabra not in lista:
            if palabra is None:
                raise ErrorIngenuo("se esperaba " + categoria + " pero termino la oracion")
            raise ErrorIngenuo("se esperaba " + categoria + " pero se encontro '" + palabra + "'")
        self.pos += 1
        return Nodo(categoria + ": " + palabra)

   
    def oracion(self):
        nodo = Nodo("oracion")
        if self.actual() in ADVERBIOS:
            nodo.agregar(self.consumir("ADV", ADVERBIOS))
        nodo.agregar(self.grupo_nominal())
        nodo.agregar(self.grupo_verbal())
        if self.actual() is not None:
            raise ErrorIngenuo("sobro la palabra '" + self.actual() + "'")
        return nodo


    def grupo_nominal(self):
        nodo = Nodo("grupo_nominal")
        nodo.agregar(self.consumir("DET", DETERMINANTES))
        if self.actual() in ADJETIVOS:
            nodo.agregar(self.consumir("ADJ", ADJETIVOS))
        nodo.agregar(self.consumir("SUST", SUSTANTIVOS))
        if self.actual() in ADJETIVOS:
            nodo.agregar(self.consumir("ADJ", ADJETIVOS))
        if self.actual() in PREPOSICIONES:
            nodo.agregar(self.frase_prep())
        if self.actual() == "que":
            nodo.agregar(self.subordinada())
        return nodo

    def grupo_verbal(self):
        nodo = Nodo("grupo_verbal")
        nodo.agregar(self.consumir("VERBO", VERBOS))
        if self.actual() in DETERMINANTES:
            nodo.agregar(self.grupo_nominal())
        if self.actual() in ADVERBIOS:
            nodo.agregar(self.consumir("ADV", ADVERBIOS))
        return nodo


    def frase_prep(self):
        nodo = Nodo("frase_prep")
        nodo.agregar(self.consumir("PREP", PREPOSICIONES))
        nodo.agregar(self.grupo_nominal())
        return nodo

    def subordinada(self):
        nodo = Nodo("subordinada")
        nodo.agregar(self.consumir("QUE", ["que"]))
        if self.actual() in DETERMINANTES:        # "que la maestra mira"
            nodo.agregar(self.grupo_nominal())
            nodo.agregar(self.consumir("VERBO", VERBOS))
        else:                                     # "que lee un libro"
            nodo.agregar(self.grupo_verbal())
        return nodo


def analizar_ingenuo(oracion):
    """Devuelve (aceptada, arbol, mensaje)."""
    try:
        return True, ParserIngenuo(oracion).oracion(), ""
    except ErrorIngenuo as e:
        return False, None, str(e)



CASOS = [
   
    {"oracion": "el niño lee un libro", "correcta": True},
    {"oracion": "la niña alta mira las flores rojas en el jardín", "correcta": True},
    {"oracion": "el niño que lee un libro mira la casa", "correcta": True},
    {"oracion": "los niños que la maestra mira leen un libro", "correcta": True},
    {"oracion": "el niño lee libro un", "correcta": False},

   
    {"oracion": "el niña lee un libro", "correcta": False,
     "regla": "<grupo_nominal> ::= DET SUST",
     "fenomeno": "concordancia de genero determinante-sustantivo",
     "nivel": "Tipo 2 (se puede, pero multiplicando reglas)",
     "explicacion": "DET y SUST son categorias sin genero. Para arreglarlo hay que "
                    "desdoblar la regla en 4 (ms, fs, mp, fp), como en espanol/gramatica_es.txt."},
    {"oracion": "el niño mira la casa rojo", "correcta": False,
     "regla": "<grupo_nominal> ::= DET SUST ADJ",
     "fenomeno": "concordancia de genero sustantivo-adjetivo",
     "nivel": "Tipo 2 (se puede, pero multiplicando reglas)",
     "explicacion": "El adjetivo no hereda el genero del sustantivo. Misma solucion: "
                    "una copia de la regla por cada combinacion de genero y numero."},
    {"oracion": "los niños lee un libro", "correcta": False,
     "regla": "<oracion> ::= <grupo_nominal> <grupo_verbal>",
     "fenomeno": "concordancia de numero sujeto-verbo",
     "nivel": "Tipo 2 (se puede, pero multiplicando reglas)",
     "explicacion": "La regla no relaciona el numero del sujeto con el del verbo. "
                    "Hay que separar oracion en singular y oracion en plural."},
    {"oracion": "los niños que la maestra mira lee un libro", "correcta": False,
     "regla": "<grupo_nominal> ::= DET SUST <subordinada>",
     "fenomeno": "concordancia a distancia (sujeto y verbo separados por una subordinada)",
     "nivel": "Tipo 2 (no es Tipo 3: hace falta memoria tipo pila)",
     "explicacion": "Entre 'niños' y 'lee' cabe una subordinada de cualquier largo. Un automata "
                    "finito no puede recordarlo; una CFG si, pero arrastrando el numero por todas "
                    "las reglas intermedias."},

   
    {"oracion": "el niño y la niña leen un libro", "correcta": True,
     "regla": "<grupo_nominal> ::= <grupo_nominal> \"y\" <grupo_nominal>",
     "fenomeno": "coordinacion (recursion por la izquierda)",
     "nivel": "Tipo 2 (limite del parser descendente, no de la CFG)",
     "explicacion": "La regla natural empieza llamandose a si misma, y un parser descendente "
                    "recursivo entraria en un ciclo infinito. Ademas singular + singular debe "
                    "dar plural, cosa que la regla tampoco expresa."},
    {"oracion": "el niño y la niña son alto y alta respectivamente", "correcta": True,
     "regla": "ninguna regla libre de contexto lo cubre en general",
     "fenomeno": "dependencias cruzadas",
     "nivel": "Tipo 1 (sensible al contexto)",
     "explicacion": "El primer adjetivo concuerda con el primer sustantivo y el segundo con el "
                    "segundo: las dependencias se cruzan en vez de anidarse. Es el patron del "
                    "lenguaje copia (ww), que no es libre de contexto."},

    
    {"oracion": "la maestra busca el libro en la mesa", "correcta": True, "ambigua": True,
     "regla": "<grupo_nominal> ::= ... [ <frase_prep> ]",
     "fenomeno": "ambiguedad estructural",
     "nivel": "Tipo 2 (gramatica ambigua, no es LL(1))",
     "explicacion": "'en la mesa' puede ir con 'el libro' (el libro que esta en la mesa) o con "
                    "'busca' (busca sobre la mesa). El parser siempre lo pega al sustantivo y "
                    "devuelve un solo arbol de los dos posibles."},
]


def paso1_minic():
    print("=" * 60)
    print("PASO 1: una oracion en espanol con el parser del mini-C")
    print("=" * 60)
    for oracion in ["el perro mira la casa", "el niño lee un libro"]:
        print("\nEntrada:", oracion)
        tokens, errores = analisis_lexico(oracion)
        print("  Tokens:", tokens)
        if errores:
            print("  " + errores[0])
            continue
        try:
            analizar(tokens)
        except ErrorSintactico as e:
            print("  " + str(e))
    print("\nConclusion: para el lexer del mini-C toda palabra es un ID y la 'ñ'")
    print("ni siquiera es un caracter valido. En espanol la categoria de una")
    print("palabra no se sabe por su forma: hace falta un vocabulario.")

    return {"oracion": "el perro mira la casa",
            "regla": "<instruccion> ::= <declaracion> | <asignacion> | <condicional> | <ciclo>",
            "fenomeno": "categorias de las palabras",
            "nivel": "Tipo 3 (nivel lexico)",
            "explicacion": "Las expresiones regulares del lexer clasifican por la forma (letras = ID). "
                           "En espanol sustantivos, verbos y adjetivos tienen la misma forma, asi que "
                           "se necesita un diccionario."}


def paso2_ingenua():
    print("\n" + "=" * 60)
    print("PASO 2: gramatica ingenua del espanol (sin genero ni numero)")
    print("=" * 60)
    fallas = []
    for caso in CASOS:
        aceptada, arbol, mensaje = analizar_ingenuo(caso["oracion"])

        if caso.get("ambigua"):
            estado = "FALLA (acepta, pero solo un arbol)"
        elif aceptada == caso["correcta"]:
            estado = "OK"
        elif aceptada:
            estado = "FALLA (acepta una oracion incorrecta)"
        else:
            estado = "FALLA (rechaza una oracion correcta)"

        print("\nOracion  :", caso["oracion"])
        print("Deberia  :", "aceptar" if caso["correcta"] else "rechazar")
        print("Resultado:", "acepta" if aceptada else "rechaza (" + mensaje + ")")
        print("Estado   :", estado)

        if estado != "OK":
            print("Regla    :", caso["regla"])
            print("Fenomeno :", caso["fenomeno"])
            print("Nivel    :", caso["nivel"])
            if caso.get("ambigua"):
                imprimir_arbol(arbol)
            fallas.append(caso)
    return fallas


def paso3_guardar(fallas):
    ruta = os.path.join(RAIZ, "pruebas", "fallas.csv")
    archivo = open(ruta, "w", newline="", encoding="utf-8")
    escritor = csv.writer(archivo)
    escritor.writerow(["oracion", "regla_que_falla", "fenomeno", "nivel_chomsky", "explicacion"])
    for f in fallas:
        escritor.writerow([f["oracion"], f["regla"], f["fenomeno"], f["nivel"], f["explicacion"]])
    archivo.close()
    print("\n" + "=" * 60)
    print("PASO 3:", len(fallas), "fallas guardadas en pruebas/fallas.csv")
    print("=" * 60)


if __name__ == "__main__":
    falla_minic = paso1_minic()
    fallas = paso2_ingenua()
    paso3_guardar([falla_minic] + fallas)
