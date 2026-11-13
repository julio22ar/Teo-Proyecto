"""Estructuras y utilidades para visualizar árboles sintácticos."""

from pathlib import Path
import shutil
import subprocess
import tempfile


class Nodo:
    def __init__(self, etiqueta):
        self.etiqueta = str(etiqueta)
        self.hijos = []

    def agregar(self, hijo):
        self.hijos.append(hijo)


def imprimir_arbol(nodo, nivel=0):
    """Imprime el árbol en consola usando sangría para cada nivel."""
    print("   " * nivel + "|- " + nodo.etiqueta)
    for hijo in nodo.hijos:
        imprimir_arbol(hijo, nivel + 1)


def _escapar_dot(texto):
    """Escapa caracteres especiales para etiquetas de Graphviz DOT."""
    return (str(texto).replace("\\", "\\\\")
            .replace('"', '\\"').replace("\n", "\\n"))


def _a_dot(raiz):
    """Serializa recursivamente un Nodo como un grafo dirigido DOT."""
    lineas = [
        "digraph ArbolSintactico {",
        '  graph [ordering="out", ranksep="0.45", nodesep="0.25"];',
        '  node [shape=box, style="rounded,filled", fillcolor="#EAF2F8", '
        'color="#315B7D", fontname="Arial", fontsize=10];',
        '  edge [color="#718096"];',
    ]
    contador = 0

    def recorrer(nodo):
        nonlocal contador
        actual = contador
        contador += 1
        lineas.append(f'  n{actual} [label="{_escapar_dot(nodo.etiqueta)}"];')
        for hijo in nodo.hijos:
            hijo_id = recorrer(hijo)
            lineas.append(f"  n{actual} -> n{hijo_id};")
        return actual

    recorrer(raiz)
    lineas.append("}")
    return "\n".join(lineas) + "\n"


def dibujar_arbol(nodo, nombre_archivo="arbol_sintactico", formato="png", abrir=False):
    """Dibuja un árbol sintáctico usando Graphviz.

    Args:
        nodo: raíz de tipo Nodo.
        nombre_archivo: ruta destino sin extensión, o con extensión .png/.svg.
        formato: formato de salida ('png' o 'svg').
        abrir: intenta abrir el archivo generado con la aplicación del sistema.

    Returns:
        Ruta del archivo renderizado. Si Graphviz no está instalado, guarda
        la especificación .dot y devuelve esa ruta para que no se pierda el árbol.

    Raises:
        TypeError: cuando nodo no es un Nodo.
        ValueError: cuando el formato no es png o svg.
        RuntimeError: cuando Graphviz está instalado pero no puede renderizar.
    """
    if not isinstance(nodo, Nodo):
        raise TypeError("nodo debe ser una instancia de Nodo.")
    formato = str(formato).lower()
    if formato not in {"png", "svg"}:
        raise ValueError("El formato debe ser 'png' o 'svg'.")

    destino = Path(nombre_archivo).expanduser()
    if destino.suffix.lower() in {".png", ".svg", ".dot"}:
        destino = destino.with_suffix("")
    destino.parent.mkdir(parents=True, exist_ok=True)
    contenido_dot = _a_dot(nodo)
    ejecutable = shutil.which("dot")

    if ejecutable is None:
        ruta_dot = destino.with_suffix(".dot")
        ruta_dot.write_text(contenido_dot, encoding="utf-8")
        return ruta_dot

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".dot", delete=False
    ) as temporal:
        temporal.write(contenido_dot)
        ruta_temporal = Path(temporal.name)

    salida = destino.with_suffix("." + formato)
    try:
        proceso = subprocess.run(
            [ejecutable, f"-T{formato}", str(ruta_temporal), "-o", str(salida)],
            check=False, capture_output=True, text=True, encoding="utf-8"
        )
        if proceso.returncode != 0:
            detalle = proceso.stderr.strip() or "Error desconocido de Graphviz."
            raise RuntimeError(f"Graphviz no pudo generar el árbol: {detalle}")
    finally:
        ruta_temporal.unlink(missing_ok=True)

    if abrir:
        try:
            import os
            if hasattr(os, "startfile"):
                os.startfile(str(salida))
            elif shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(salida)])
            elif shutil.which("open"):
                subprocess.Popen(["open", str(salida)])
        except OSError:
            pass
    return salida
