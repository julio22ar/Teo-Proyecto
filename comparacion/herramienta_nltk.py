import re
import sys

import nltk
from nltk.corpus import cess_esp

def simplificar(etiqueta):
    etiqueta = etiqueta.lower()
    if etiqueta.startswith("pr"):
        return "rel"       # pronombre relativo: que
    if etiqueta.startswith("pp"):
        return "pron"      # pronombre personal: la, lo, ella
    if etiqueta.startswith("cs"):
        return "rel"       # "que" como conjuncion subordinante
    if etiqueta.startswith("rn"):
        return "neg"       # no
    if etiqueta.startswith("np"):
        return "n"         # nombre propio = sustantivo
    primera = etiqueta[0]
    categorias = {
        "d": "det", "n": "n", "a": "adj", "v": "v", "r": "adv",
        "s": "prep", "c": "conj", "p": "pron", "f": "punt",
    }
    return categorias.get(primera, "otro")


# 1: el etiquetador (se entrena una sola vez y se guarda)

_etiquetador = None


def obtener_etiquetador():
    global _etiquetador
    if _etiquetador is None:
        oraciones = []
        for oracion in cess_esp.tagged_sents():
            limpia = [(palabra.lower(), simplificar(etiqueta))
                      for palabra, etiqueta in oracion
                      if palabra != "*0*"]  
            oraciones.append(limpia)

        
        reglas = nltk.RegexpTagger([
            (r".*mente$", "adv"),
            (r".*(aron|ieron|ó|ió|an|en)$", "v"),
            (r".*", "n"),                     
        ])
        unigramas = nltk.UnigramTagger(oraciones, backoff=reglas)
        _etiquetador = nltk.BigramTagger(oraciones, backoff=unigramas)
    return _etiquetador


def etiquetar(oracion):
    """Devuelve la lista [(palabra, categoria), ...] sin el punto final."""
    palabras = re.findall(r"\w+", oracion.lower())
    return obtener_etiquetador().tag(palabras)


# 2: gramatica general del espanol (sobre las categorias)

GRAMATICA = nltk.CFG.fromstring("""
    O    -> SN SV | SV | ADVS O | O CONJ O
    SN   -> DET NOM | NOM | PRON | SN CONJ SN
    NOM  -> N | ADJS NOM | NOM ADJS | NOM SP | NOM REL
    ADJS -> ADJ | ADJ CONJ ADJS
    SP   -> PREP SN
    REL  -> RELP SV | RELP SN V
    SV   -> V | V SN | V ADJS | SV SP | SV ADVS | ADVS SV
    SV   -> NEG SV | PRON V
    ADVS -> ADV
    DET  -> 'det'
    N    -> 'n'
    ADJ  -> 'adj'
    V    -> 'v'
    ADV  -> 'adv'
    PREP -> 'prep'
    CONJ -> 'conj'
    PRON -> 'pron'
    RELP -> 'rel'
    NEG  -> 'neg'
""")

_parser = nltk.ChartParser(GRAMATICA)


def analizar_nltk(oracion, max_arboles=50):
    """Analiza una oracion con NLTK.

    Devuelve (aceptada, detalle):
      aceptada -> True si NLTK arma al menos un arbol, False si no.
      detalle  -> texto con las categorias que asigno y cuantos arboles hallo.
    """
    etiquetas = etiquetar(oracion)
    categorias = [categoria for _, categoria in etiquetas]
    texto_etiquetas = " ".join(palabra + "/" + cat for palabra, cat in etiquetas)

    if not categorias:
        return False, "Oracion vacia."

    try:
        arboles = []
        for arbol in _parser.parse(categorias):
            arboles.append(arbol)
            if len(arboles) >= max_arboles:   # tope para no tardar con oraciones ambiguas
                break
    except ValueError as error:
        # Pasa si aparece una categoria que la gramatica no tiene (ej: "otro")
        return False, "Etiquetas: " + texto_etiquetas + " | Sin arbol: " + str(error)

    if arboles:
        cantidad = str(len(arboles)) + ("+" if len(arboles) >= max_arboles else "")
        return True, "Etiquetas: " + texto_etiquetas + " | Arboles: " + cantidad
    return False, "Etiquetas: " + texto_etiquetas + " | Sin arbol posible"


def primer_arbol(oracion):
    """Devuelve el primer arbol de NLTK (o None), util para mostrarlo en la demo."""
    categorias = [c for _, c in etiquetar(oracion)]
    try:
        return next(_parser.parse(categorias), None)
    except ValueError:
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ejemplos = [" ".join(sys.argv[1:])]
    else:
        ejemplos = [
            "El niño lee un libro.",
            "La niña alta mira las flores rojas en el jardín.",
            "El niño que lee un libro mira la casa.",
            "El niño y la niña leen un libro.",
            "El niño lee.",
            "El niña lee un libro.",
            "Niño el lee un libro.",
        ]
    print("Entrenando el etiquetador con cess_esp (unos segundos)...\n")
    for oracion in ejemplos:
        aceptada, detalle = analizar_nltk(oracion)
        print(("ACEPTA " if aceptada else "RECHAZA") + " | " + oracion)
        print("        " + detalle)
        if aceptada and len(ejemplos) == 1:
            primer_arbol(oracion).pretty_print()
        print()
