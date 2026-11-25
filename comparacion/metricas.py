# Metricas de la comparacion (Fase 2). Integrante 4: Diego.
#
# Lee comparacion/resultados.csv (lo genera comparar.py) y calcula, por cada
# sistema y por cada nivel (1, 2, 3):
#   - precision, cobertura (recall), tasa de rechazo correcto
#   - falsos positivos (fp) y falsos negativos (fn)
# Guarda comparacion/metricas.csv con las columnas que usa graficas.py (Everth):
#   sistema,nivel,precision,recall,tasa_rechazo_correcto,fp,fn
# Las tasas se guardan como proporciones (0 a 1); vacias si no estan definidas.
#
# Convencion (clase positiva = "aceptar"), igual que en main.py:
#   TP: esperado aceptar y el sistema acepta
#   FN: esperado aceptar y el sistema rechaza
#   FP: esperado rechazar y el sistema acepta
#   TN: esperado rechazar y el sistema rechaza
#
# Uso (desde la raiz):
#   python -m comparacion.metricas

import csv
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVO_RESULTADOS = os.path.join(RAIZ, "comparacion", "resultados.csv")
ARCHIVO_METRICAS = os.path.join(RAIZ, "comparacion", "metricas.csv")

SISTEMAS = ["parser_propio", "spacy", "nltk"]
NIVELES = ["1", "2", "3"]


def _tasa(numerador, denominador):
    """Proporcion 0 a 1, o None si el denominador es 0 (indefinida)."""
    if denominador == 0:
        return None
    return numerador / denominador


def contar(filas, sistema):
    """Cuenta tp, fn, fp, tn para un sistema sobre una lista de filas."""
    tp = fn = fp = tn = 0
    for fila in filas:
        esperado = fila["esperado"]
        predicho = fila[sistema]
        if esperado == "aceptar" and predicho == "aceptar":
            tp += 1
        elif esperado == "aceptar" and predicho == "rechazar":
            fn += 1
        elif esperado == "rechazar" and predicho == "aceptar":
            fp += 1
        else:
            tn += 1
    return tp, fn, fp, tn


def metricas_de(filas, sistema):
    """Devuelve el diccionario de metricas de un sistema sobre esas filas."""
    tp, fn, fp, tn = contar(filas, sistema)
    return {
        "precision": _tasa(tp, tp + fp),
        "recall": _tasa(tp, tp + fn),
        "tasa_rechazo_correcto": _tasa(tn, tn + fp),
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "tn": tn,
    }


def _texto_tasa(valor):
    """Formatea una proporcion para el CSV; vacio si es None."""
    if valor is None:
        return ""
    return format(valor, ".4f")


def main():
    if not os.path.isfile(ARCHIVO_RESULTADOS):
        print("No se encontro comparacion/resultados.csv.")
        print("Primero ejecute: python -m comparacion.comparar")
        return

    with open(ARCHIVO_RESULTADOS, "r", encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    # 1) Guardar el CSV por sistema y nivel (para las graficas de Everth).
    columnas = ["sistema", "nivel", "precision", "recall",
                "tasa_rechazo_correcto", "fp", "fn"]
    with open(ARCHIVO_METRICAS, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for sistema in SISTEMAS:
            for nivel in NIVELES:
                filas_nivel = [f for f in filas if f["nivel"] == nivel]
                m = metricas_de(filas_nivel, sistema)
                escritor.writerow({
                    "sistema": sistema,
                    "nivel": nivel,
                    "precision": _texto_tasa(m["precision"]),
                    "recall": _texto_tasa(m["recall"]),
                    "tasa_rechazo_correcto": _texto_tasa(m["tasa_rechazo_correcto"]),
                    "fp": m["fp"],
                    "fn": m["fn"],
                })
    print("Metricas guardadas en: comparacion/metricas.csv")

    # 2) Imprimir un resumen global en pantalla (para el informe y la demo).
    print("\n" + "=" * 64)
    print(" RESUMEN GLOBAL (las 60 oraciones)")
    print("=" * 64)
    print(" sistema         precision   recall   rechazo_correcto   fp   fn")
    print(" " + "-" * 62)
    for sistema in SISTEMAS:
        m = metricas_de(filas, sistema)
        def p(v):
            return "   N/D " if v is None else format(v, ".2%").rjust(7)
        print(" " + sistema.ljust(15) +
              p(m["precision"]) + "  " +
              p(m["recall"]) + "   " +
              p(m["tasa_rechazo_correcto"]).rjust(10) + "    " +
              str(m["fp"]).rjust(3) + "  " + str(m["fn"]).rjust(3))

    print("\nClasificacion de errores (clase positiva = 'aceptar'):")
    print("  - Falso positivo (fp): el sistema ACEPTA una oracion que debia rechazar.")
    print("  - Falso negativo (fn): el sistema RECHAZA una oracion que debia aceptar.")
    print("\nLectura rapida: una tasa de rechazo correcto alta y pocos fp indican")
    print("que el sistema distingue lo agramatical; spaCy no rechaza, asi que su")
    print("rechazo correcto es 0 y acumula falsos positivos.")


if __name__ == "__main__":
    main()
