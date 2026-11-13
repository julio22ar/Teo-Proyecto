import csv
import os
import sys

# Asegurar codificacion UTF-8 para caracteres en espanol
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from espanol.parser_es import analizar_oracion

ARCHIVO_FALLAS = os.path.join(RAIZ, "pruebas", "fallas.csv")
MODELO_SPACY = "es_core_news_sm"


def cargar_spacy():
    """Carga el modelo en espanol de spaCy."""
    try:
        import spacy
    except ImportError:
        print("Falta instalar spacy: pip install spacy")
        return None
    try:
        return spacy.load(MODELO_SPACY)
    except OSError:
        print("Falta descargar el modelo: python -m spacy download " + MODELO_SPACY)
        return None


def leer_fallas():
    """Lee las oraciones de prueba desde fallas.csv."""
    filas = []
    with open(ARCHIVO_FALLAS, "r", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila.get("oracion"):
                filas.append(fila)
    return filas


def analisis_con_nuestra_cfg(oracion):
    aceptada, _arbol, mensaje = analizar_oracion(oracion)
    return aceptada, mensaje


def analisis_con_spacy(nlp, oracion):
    doc = nlp(oracion)
    tokens = []
    for token in doc:
        tokens.append({
            "palabra": token.text,
            "pos": token.pos_,
            "dep": token.dep_,
            "head": token.head.text,
        })
    return tokens


def imprimir_tabla_spacy(tokens):
    encabezado = ("PALABRA", "CATEGORIA", "FUNCION", "DEPENDE DE")
    print("   {:<14}{:<12}{:<12}{}".format(*encabezado))
    print("   " + "-" * 48)
    for t in tokens:
        print("   {:<14}{:<12}{:<12}{}".format(
            t["palabra"], t["pos"], t["dep"], t["head"]))


def main():
    print("=" * 64)
    print(" DEMO FASE 1: spaCy vs. Gramatica Libre de Contexto")
    print("=" * 64)

    nlp = cargar_spacy()
    if nlp is None:
        return

    fallas = leer_fallas()
    analizadas_por_spacy = 0
    rechazadas_por_cfg = 0

    for i, fila in enumerate(fallas, start=1):
        oracion = fila["oracion"]
        print("\n" + "-" * 64)
        print(f"[{i}] Oracion: \"{oracion}\"")
        print("    Fenomeno: " + fila.get("fenomeno", ""))
        print("    Nivel Chomsky: " + fila.get("nivel_chomsky", ""))

        # 1) Prueba con nuestro parser CFG
        aceptada, mensaje = analisis_con_nuestra_cfg(oracion)
        if aceptada:
            print("\n  Nuestra CFG -> ACEPTA")
        else:
            rechazadas_por_cfg += 1
            print("\n  Nuestra CFG -> RECHAZA")
            print("                 Motivo: " + str(mensaje))
            print("                 Regla: " + fila.get("regla_que_falla", ""))

        # 2) Prueba con spaCy
        print("\n  spaCy       -> Analisis sintactico:")
        tokens = analisis_con_spacy(nlp, oracion)
        imprimir_tabla_spacy(tokens)
        analizadas_por_spacy += 1

    # Resumen
    print("\n" + "=" * 64)
    print(" RESUMEN")
    print("=" * 64)
    print(" Oraciones probadas:              " + str(len(fallas)))
    print(" Rechazadas por nuestra CFG:      " + str(rechazadas_por_cfg))
    print(" Analizadas por spaCy:            " + str(analizadas_por_spacy))
    print("\n Conclusion: La CFG se rige por reglas formales estrictas y rechaza")
    print(" estructuras no contempladas (o ambiguas). spaCy utiliza un modelo")
    print(" estadistico que le permite procesar y anotar cualquier oracion.")


if __name__ == "__main__":
    main()