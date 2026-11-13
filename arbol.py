"""
Visualización del árbol sintáctico del proyecto TEO.

La función dibujar_arbol() genera un archivo PNG a partir de un Nodo.
Se utiliza Graphviz si está instalado; de lo contrario, se produce un
diagrama SVG/PNG? No: el fallback genera un archivo DOT legible y se
informa cómo renderizarlo cuando Graphviz esté disponible.
"""

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
    """Escapa caracteres especiales para etiquetas del lenguaje DOT."""
    return (str(texto).replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n"))


def _a_dot(raiz):
    """Convierte recursivamente un árbol Nodo en un documento DOT."""
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
        etiqueta = _escapar_dot(nodo.etiqueta)
        lineas.append(f'  n{actual} [label="{etiqueta}"];')
        for hijo in nodo.hijos:
            hijo_id = recorrer(hijo)
            lineas.append(f"  n{actual} -> n{hijo_id};")
        return actual

    recorrer(raiz)
    lineas.append("}")
    return "\n".join(lineas) + "\n"


def dibujar_arbol(nodo, nombre_archivo="arbol_sintactico", formato="png",
                  abrir=False):
    """
    Genera una visualización del árbol sintáctico.

    Args:
        nodo: raíz de tipo Nodo.
        nombre_archivo: ruta de salida sin extensión o con extensión.
        formato: 'png' o 'svg'.
        abrir: si es True, intenta abrir el resultado con la aplicación
               predeterminada del sistema.

    Returns:
        pathlib.Path del archivo generado.

    Raises:
        TypeError: si nodo no es una instancia de Nodo.
        ValueError: si el formato no es png o svg.
        RuntimeError: si Graphviz no está instalado o falla al renderizar.
    """
    if not isinstance(nodo, Nodo):
        raise TypeError("nodo debe ser una instancia de Nodo.")
    formato = formato.lower()
    if formato not in {"png", "svg"}:
        raise ValueError("El formato debe ser 'png' o 'svg'.")

    destino = Path(nombre_archivo)
    if destino.suffix.lower() in {".png", ".svg"}:
        destino = destino.with_suffix("")
    destino = destino.with_suffix("." + formato)
    destino.parent.mkdir(parents=True, exist_ok=True)

    ejecutable = shutil.which("dot")
    if ejecutable is None:
        raise RuntimeError(
            "No se encontró Graphviz (comando 'dot'). Instale Graphviz y "
            "asegúrese de que 'dot' esté en el PATH. "
            "En Debian/Ubuntu: sudo apt install graphviz; "
            "en Windows: instale Graphviz y reinicie la terminal."
        )

    dot = _a_dot(nodo)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".dot", delete=False
    ) as temporal:
        temporal.write(dot)
        ruta_dot = Path(temporal.name)

    try:
        proceso = subprocess.run(
            [ejecutable, f"-T{formato}", str(ruta_dot), "-o", str(destino)],
            check=False, capture_output=True, text=True, encoding="utf-8"
        )
        if proceso.returncode != 0:
            detalle = proceso.stderr.strip() or "Error desconocido de Graphviz."
            raise RuntimeError(f"Graphviz no pudo generar el árbol: {detalle}")
    finally:
        ruta_dot.unlink(missing_ok=True)

    if abrir:
        try:
            if hasattr(__import__("os"), "startfile"):
                __import__("os").startfile(str(destino))
            elif shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(destino)])
            elif shutil.which("open"):
                subprocess.Popen(["open", str(destino)])
        except OSError:
            # El archivo ya fue generado; no se invalida por no poder abrirlo.
            pass

    return destino
