# Comparacion de las 60 oraciones con los tres sistemas (Fase 2).
# Integrante 4: Diego.
#
# Corre cada oracion de pruebas/oraciones.csv por:
#   - parser_propio : nuestro parser del espanol (analizar_oracion).
#   - spacy         : spaCy con el modelo es_core_news_sm.
#   - nltk          : la segunda herramienta de Alex (analizar_nltk).
# Guarda la decision (aceptar/rechazar) y el tiempo de cada uno en
# comparacion/resultados.csv, que luego lee metricas.py.
#
# Nota importante sobre spaCy: spaCy es un etiquetador/analizador estadistico
# que SIEMPRE le asigna un analisis a cualquier texto; no tiene un juicio de
# "gramatical / no gramatical". Por eso aqui su decision es siempre "aceptar".
# Esa es justamente una conclusion de la comparacion: un parser formal puede
# rechazar, un modelo estadistico de dependencias no.
#
# Uso (desde la raiz):
#   python -m comparacion.comparar

import csv
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from espanol.parser_es import analizar_oracion

ARCHIVO_ORACIONES = os.path.join(RAIZ, "pruebas", "oraciones.csv")
ARCHIVO_RESULTADOS = os.path.join(RAIZ, "comparacion", "resultados.csv")
MODELO_SPACY = "es_core_news_sm"


def decision_parser_propio(oracion):
    """Nuestro parser: acepta si analizar_oracion devuelve True."""
    inicio = time.perf_counter()
    aceptada, _arbol, _mensaje = analizar_oracion(oracion)
    ms = (time.perf_counter() - inicio) * 1000
    return ("aceptar" if aceptada else "rechazar"), ms


def cargar_spacy():
    """Carga spaCy y el modelo de espanol, o None si falta algo."""
    try:
        import spacy
    except ImportError:
        print("Falta spaCy: pip install spacy")
        return None
    try:
        return spacy.load(MODELO_SPACY)
    except OSError:
        print("Falta el modelo: python -m spacy download " + MODELO_SPACY)
        return None


def decision_spacy(nlp, oracion):
    """spaCy siempre produce un analisis -> siempre 'aceptar'."""
    inicio = time.perf_counter()
    nlp(oracion)
    ms = (time.perf_counter() - inicio) * 1000
    return "aceptar", ms


def cargar_nltk():
    """Devuelve la funcion analizar_nltk de Alex, o None si falta nltk."""
    try:
        from comparacion.herramienta_nltk import analizar_nltk
    except ImportError:
        print("Falta nltk o el corpus. Instale: pip install nltk")
        print("y descargue: python -c \"import nltk; nltk.download('cess_esp')\"")
        return None
    return analizar_nltk


def decision_nltk(analizar_nltk, oracion):
    """NLTK (CFG de Alex): acepta si arma al menos un arbol."""
    inicio = time.perf_counter()
    aceptada, _detalle = analizar_nltk(oracion)
    ms = (time.perf_counter() - inicio) * 1000
    return ("aceptar" if aceptada else "rechazar"), ms


def leer_oraciones():
    with open(ARCHIVO_ORACIONES, "r", encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def main():
    print("Cargando herramientas (spaCy y NLTK tardan unos segundos)...")
    nlp = cargar_spacy()
    analizar_nltk = cargar_nltk()
    if nlp is None or analizar_nltk is None:
        print("No se pueden cargar las tres herramientas; se cancela.")
        return

    filas = leer_oraciones()
    resultados = []
    suma_ms = {"parser_propio": 0.0, "spacy": 0.0, "nltk": 0.0}

    for fila in filas:
        oracion = fila["oracion"]
        d_parser, t_parser = decision_parser_propio(oracion)
        d_spacy, t_spacy = decision_spacy(nlp, oracion)
        d_nltk, t_nltk = decision_nltk(analizar_nltk, oracion)

        suma_ms["parser_propio"] += t_parser
        suma_ms["spacy"] += t_spacy
        suma_ms["nltk"] += t_nltk

        resultados.append({
            "id": fila["id"],
            "oracion": oracion,
            "nivel": fila["nivel"],
            "esperado": fila["esperado"],
            "parser_propio": d_parser,
            "spacy": d_spacy,
            "nltk": d_nltk,
            "ms_parser_propio": round(t_parser, 3),
            "ms_spacy": round(t_spacy, 3),
            "ms_nltk": round(t_nltk, 3),
        })

    columnas = ["id", "oracion", "nivel", "esperado",
                "parser_propio", "spacy", "nltk",
                "ms_parser_propio", "ms_spacy", "ms_nltk"]
    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(resultados)

    total = len(filas)
    print("\nProcesadas " + str(total) + " oraciones.")
    print("Resultados guardados en: comparacion/resultados.csv")
    print("\nTiempo promedio por oracion (costo computacional):")
    for sistema in ("parser_propio", "spacy", "nltk"):
        promedio = suma_ms[sistema] / total if total else 0
        print("  " + sistema.ljust(14) + ": " + format(promedio, ".3f") + " ms")


if __name__ == "__main__":
    main()
