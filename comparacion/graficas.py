"""Gráficas reproducibles para el informe de Fase 2.

Uso desde la raíz:
    python -m comparacion.graficas
    python -m comparacion.graficas --metricas comparacion/metricas.csv

El CSV de métricas debe tener una fila por sistema y nivel (1, 2, 3):
sistema,nivel,precision,recall,tasa_rechazo_correcto,fp,fn
Las tasas numéricas se leen como proporciones por defecto. Use
--escala porcentaje si el CSV guarda 0–100, o agregue % a cada tasa.
Una tasa indefinida se puede dejar vacía.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
NIVELES = ("1", "2", "3")
COLORES = ("#176A9A", "#158374", "#BA582B")
TASAS = ("precision", "recall", "tasa_rechazo_correcto")
CAMPOS = {"sistema", "nivel", *TASAS, "fp", "fn"}


def leer_csv(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        return set(lector.fieldnames or []), list(lector)


def leer_tasa(texto, escala):
    texto = texto.strip()
    if not texto:
        return None
    con_signo = texto.endswith("%")
    tasa = float(texto.removesuffix("%"))
    if not con_signo and escala == "proporcion":
        tasa *= 100
    if not 0 <= tasa <= 100:
        raise ValueError("Tasa fuera de rango. Revise --escala.")
    return tasa


def leer_metricas(ruta, escala):
    encabezados, filas = leer_csv(ruta)
    if faltantes := CAMPOS - encabezados:
        raise ValueError("Faltan columnas: " + ", ".join(sorted(faltantes)))

    sistemas = {}
    for numero_fila, fila in enumerate(filas, start=2):
        try:
            sistema = fila["sistema"].strip()
            nivel = fila["nivel"].strip()
            if nivel in {"total", "global"}:
                continue
            if not sistema or nivel not in NIVELES:
                raise ValueError("Se espera un sistema y un nivel del 1 al 3.")
            datos = sistemas.setdefault(sistema, {})
            if nivel in datos:
                raise ValueError("Sistema y nivel repetidos.")
            tasas = {campo: leer_tasa(fila[campo], escala) for campo in TASAS}
            errores = {campo: int(fila[campo]) for campo in ("fp", "fn")}
            if min(errores.values()) < 0:
                raise ValueError("Los conteos de errores no pueden ser negativos.")
            datos[nivel] = {**tasas, **errores}
        except (ValueError, AttributeError, TypeError) as error:
            raise ValueError(f"{ruta.name}, fila {numero_fila}: {error}") from error

    if not sistemas:
        raise ValueError("El CSV no contiene métricas por nivel.")
    for sistema, datos in sistemas.items():
        if set(datos) != set(NIVELES):
            raise ValueError(f"Faltan niveles del 1 al 3 para {sistema}.")
    return sistemas


def barras(ax, categorias, series, porcentaje=False):
    ancho = 0.72 / len(series)
    for indice, (nombre, valores) in enumerate(series):
        centros = [x + (indice - (len(series) - 1) / 2) * ancho
                   for x in range(len(categorias))]
        posiciones = [x for x, v in zip(centros, valores) if v is not None]
        alturas = [v for v in valores if v is not None]
        grupo = ax.bar(posiciones, alturas, ancho * 0.88,
                       label=nombre, color=COLORES[indice % len(COLORES)])
        etiquetas = [f"{v:.1f}".rstrip("0").rstrip(".") + "%" if porcentaje
                     else str(v) for v in alturas]
        ax.bar_label(grupo, labels=etiquetas, padding=4, fontsize=9)
        for x, valor in zip(centros, valores):
            if valor is None:
                ax.annotate("N/D", (x, 0), xytext=(0, 4),
                            textcoords="offset points", ha="center", fontsize=9)
    ax.set_xticks(range(len(categorias)), categorias)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#DFE8EF")
    ax.spines[["top", "right"]].set_visible(False)
    if porcentaje:
        ax.set_ylim(0, 116)
        ax.set_yticks(range(0, 101, 20), [f"{x}%" for x in range(0, 101, 20)])


def guardar(plt, figura, salida, nombre, fuente):
    figura.text(0.08, 0.04, fuente, fontsize=9, color="#45596A")
    ruta = salida / nombre
    figura.savefig(ruta, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    print(ruta)


def graficar_corpus(plt, salida):
    _, filas = leer_csv(RAIZ / "pruebas" / "oraciones.csv")
    conteos = Counter((fila["nivel"], fila["esperado"]) for fila in filas)
    fig, ax = plt.subplots(figsize=(7.5, 4.9))
    fig.subplots_adjust(bottom=0.17, top=0.84)
    fig.suptitle("Etiquetas del corpus por nivel", fontsize=19, fontweight="bold")
    barras(ax, [f"Nivel {n}" for n in NIVELES],
           [(e.capitalize(), [conteos[n, e] for n in NIVELES])
            for e in ("aceptar", "rechazar")])
    ax.set_ylabel("Oraciones")
    limite = max(conteos.values()) + 5
    ax.set_ylim(0, limite)
    ax.set_yticks(range(0, limite + 1, 5))
    ax.legend(loc="upper left", frameon=False)
    guardar(plt, fig, salida, "corpus_por_nivel.png", "Datos de pruebas/oraciones.csv")


def graficar_llm(plt, salida):
    with (RAIZ / "llm" / "resumen.json").open(encoding="utf-8-sig") as archivo:
        datos = json.load(archivo)
    fig, ax = plt.subplots(figsize=(7.5, 4.9))
    fig.subplots_adjust(bottom=0.17, top=0.84)
    fig.suptitle("Experimento con el modelo de lenguaje", fontsize=18, fontweight="bold")
    barras(ax, ["Exactitud frente al corpus", "Adhesión a la gramática"],
           [(m, [100 * datos[m][k] for k in ("exactitud_corpus", "adhesion_cfg")])
            for m in ("zero-shot", "few-shot")], porcentaje=True)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.04), ncol=2, frameon=False)
    guardar(plt, fig, salida, "llm_zero_few.png", "Datos de llm/resumen.json")


def graficar_comparacion(plt, salida, sistemas, fuente):
    niveles = [f"Nivel {n}" for n in NIVELES]
    grupos = [
        ("Métricas de aceptación por nivel", TASAS,
         ("Precisión", "Cobertura (recall)", "Rechazo correcto"), "metricas_por_nivel.png"),
        ("Errores de clasificación por nivel", ("fp", "fn"),
         ("Falsos positivos", "Falsos negativos"), "errores_por_nivel.png"),
    ]
    max_error = max(fila[k] for datos in sistemas.values() for fila in datos.values()
                    for k in ("fp", "fn"))
    for titulo, campos, titulos, nombre in grupos:
        fig, ejes = plt.subplots(1, len(campos), figsize=(5.2 * len(campos), 4.9))
        fig.subplots_adjust(bottom=0.17, top=0.75, wspace=0.25)
        fig.suptitle(titulo, fontsize=19, fontweight="bold")
        for ax, campo, subtitulo in zip(ejes, campos, titulos):
            barras(ax, niveles, [(s, [datos[n][campo] for n in NIVELES])
                                 for s, datos in sistemas.items()], campo in TASAS)
            ax.set_title(subtitulo)
            if campo not in TASAS:
                ax.set_ylim(0, max_error + max(2, max_error * 0.15))
                ax.yaxis.get_major_locator().set_params(integer=True)
        handles, etiquetas = ejes[0].get_legend_handles_labels()
        fig.legend(handles, etiquetas, loc="upper center", bbox_to_anchor=(0.5, 0.90),
                   ncol=min(len(sistemas), 4), frameon=False)
        guardar(plt, fig, salida, nombre, f"Datos de {fuente}")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--metricas", type=Path, help="CSV por sistema y nivel.")
    cli.add_argument("--escala", choices=("proporcion", "porcentaje"), default="proporcion")
    cli.add_argument("--salida", type=Path, default=RAIZ / "informe" / "graficas")
    args = cli.parse_args()

    ruta = args.metricas or RAIZ / "comparacion" / "metricas.csv"
    try:
        sistemas = leer_metricas(ruta, args.escala) if args.metricas or ruta.is_file() else None
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as error:
        cli.exit(1, f"Falta una dependencia ({error.name}). Ejecute python -m pip install matplotlib.\n")
    except (OSError, ValueError) as error:
        cli.exit(1, f"No se pudieron leer las métricas: {error}\n")

    args.salida.mkdir(parents=True, exist_ok=True)
    graficar_corpus(plt, args.salida)
    graficar_llm(plt, args.salida)
    if sistemas is not None:
        graficar_comparacion(plt, args.salida, sistemas, ruta.name)
    else:
        print("Gráficas de sistemas pendientes del CSV de métricas. Use --metricas para indicar la ruta.")


if __name__ == "__main__":
    main()
