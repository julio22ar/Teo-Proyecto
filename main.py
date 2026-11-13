"""Punto de entrada del proyecto TEO.

Sin argumentos muestra un menú para acceder a los módulos del proyecto.
También conserva el modo de ejecución directa:
    python main.py ruta/al/archivo.c
"""

import csv
import subprocess
import sys
from pathlib import Path

from arbol import dibujar_arbol, imprimir_arbol
from minic.lexer import analisis_lexico
from minic.parser import analizar, ErrorSintactico
from espanol.parser_es import analizar_oracion

RAIZ = Path(__file__).resolve().parent
SALIDAS = RAIZ / "salidas"


def _guardar_arbol(arbol, nombre):
    """Genera el archivo visual cuando Graphviz está disponible."""
    try:
        ruta = dibujar_arbol(arbol, SALIDAS / nombre, formato="png")
        print(f"\nÁrbol generado: {ruta.relative_to(RAIZ)}")
        if ruta.suffix == ".dot":
            print("Graphviz no está instalado; se guardó el archivo DOT. "
                  "Instale Graphviz para obtener PNG/SVG.")
    except RuntimeError as error:
        print(f"\nNo se pudo renderizar el árbol: {error}")


def procesar(entrada, dibujar=False, nombre_arbol="arbol_minic"):
    """Ejecuta lexer y parser mini-C. Devuelve True si la entrada es válida.

    El argumento dibujar se mantiene opcional para que las pruebas unitarias
    puedan llamar a procesar() sin depender de Graphviz.
    """
    print("--- ANALISIS LEXICO ---")
    tokens, errores = analisis_lexico(entrada)
    for token in tokens:
        print(token.tipo.ljust(6), ":", token.lex)
    for error in errores:
        print(error)
    if errores:
        print("\nHay errores léxicos; no se realiza el análisis sintáctico.")
        return False

    print("\n--- ANALISIS SINTACTICO ---")
    try:
        arbol = analizar(tokens)
    except ErrorSintactico as error:
        print(error)
        print("Entrada RECHAZADA.")
        return False

    imprimir_arbol(arbol)
    if dibujar:
        _guardar_arbol(arbol, nombre_arbol)
    print("\nEntrada ACEPTADA: pertenece al lenguaje mini-C definido.")
    return True


def procesar_espanol(oracion, dibujar=True):
    """Ejecuta el parser del español reducido y muestra su árbol."""
    print("--- PARSER DEL ESPAÑOL REDUCIDO ---")
    aceptada, arbol, mensaje = analizar_oracion(oracion)
    if not aceptada:
        print("Oración RECHAZADA por la gramática reducida.")
        print("Motivo:", mensaje)
        return False

    imprimir_arbol(arbol)
    if dibujar:
        _guardar_arbol(arbol, "arbol_espanol")
    print("\nOración ACEPTADA por la gramática reducida.")
    print("Nota: aceptación sintáctica no equivale a validar el significado real.")
    return True


def leer_codigo_multilinea():
    """Permite cargar archivo o pegar código hasta escribir :fin."""
    ruta = input("Ruta del archivo (Enter para pegar código): ").strip().strip('"')
    if ruta:
        archivo = Path(ruta).expanduser()
        if not archivo.is_absolute():
            archivo = (Path.cwd() / archivo).resolve()
        try:
            return archivo.read_text(encoding="utf-8")
        except OSError as error:
            print(f"No se pudo leer el archivo: {error}")
            return None

    print("Pegue el código. Escriba :fin en una línea para terminar:")
    lineas = []
    while True:
        try:
            linea = input()
        except EOFError:
            break
        if linea.strip() == ":fin":
            break
        lineas.append(linea)
    return "\n".join(lineas)


def ejecutar_pruebas_minic():
    """Ejecuta la batería de casos válidos e inválidos del mini-C."""
    ruta = RAIZ / "pruebas" / "casos_minic.py"
    if not ruta.is_file():
        print("No se encontró pruebas/casos_minic.py.")
        return
    subprocess.run([sys.executable, str(ruta)], cwd=RAIZ, check=False)


def ejecutar_demo_spacy():
    """Ejecuta la demo exploratoria spaCy de la carpeta comparacion."""
    try:
        from comparacion.demo_spacy import main as demo
    except ImportError as error:
        print("No se pudo cargar la demo de spaCy:", error)
        return
    print("Nota: esta demo usa pruebas/fallas.csv (casos exploratorios), no las 60 oraciones.")
    demo()


def evaluar_corpus_espanol():
    """Contrasta el parser del español con las etiquetas del corpus de 60 casos."""
    ruta = RAIZ / "pruebas" / "oraciones.csv"
    if not ruta.is_file():
        print("No se encontró pruebas/oraciones.csv.")
        return

    matriz = {("aceptar", "aceptar"): 0, ("aceptar", "rechazar"): 0,
              ("rechazar", "aceptar"): 0, ("rechazar", "rechazar"): 0}
    por_nivel = {}
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    for fila in filas:
        aceptada, _, _ = analizar_oracion(fila["oracion"])
        prediccion = "aceptar" if aceptada else "rechazar"
        esperado = fila["esperado"]
        matriz[(esperado, prediccion)] += 1
        nivel = fila["nivel"]
        por_nivel.setdefault(nivel, {"total": 0, "coinciden": 0, "aceptadas": 0})
        por_nivel[nivel]["total"] += 1
        por_nivel[nivel]["coinciden"] += prediccion == esperado
        por_nivel[nivel]["aceptadas"] += aceptada

    tp = matriz[("aceptar", "aceptar")]
    fn = matriz[("aceptar", "rechazar")]
    fp = matriz[("rechazar", "aceptar")]
    tn = matriz[("rechazar", "rechazar")]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    rechazo_correcto = tn / (tn + fp) if tn + fp else 0.0

    print("\n--- RESULTADOS DEL PARSER PROPIO SOBRE EL CORPUS ---")
    print(f"Oraciones procesadas: {len(filas)}")
    for nivel in sorted(por_nivel):
        datos = por_nivel[nivel]
        print(f"Nivel {nivel}: {datos['coinciden']}/{datos['total']} coincidencias; "
              f"{datos['aceptadas']} aceptadas por la CFG.")
    print("\nMatriz de confusión (referencia: columna 'esperado' del corpus):")
    print(f"  Verdaderos positivos (TP): {tp}")
    print(f"  Falsos negativos (FN):     {fn}")
    print(f"  Falsos positivos (FP):     {fp}")
    print(f"  Verdaderos negativos (TN): {tn}")
    print(f"Precisión:                 {precision:.2%}")
    print(f"Recall / cobertura:        {recall:.2%}")
    print(f"Rechazo correcto:          {rechazo_correcto:.2%}")
    print("\nInterpretación: esta comparación usa las etiquetas del corpus; no mide "
          "la capacidad de comprender todo el español.")


def ejecutar_experimento_llm():
    """Prepara el experimento LLM o lo ejecuta mediante la API configurada."""
    print("1. Preparar archivos sin consultar la API")
    print("2. Ejecutar el experimento completo (120 solicitudes API)")
    opcion = input("Seleccione una opción: ").strip()
    comando = [sys.executable, "-m", "llm.experimento"]
    if opcion == "1":
        comando.append("--preparar")
    elif opcion == "2":
        confirmacion = input(
            "Esto enviará 120 solicitudes y puede generar cargos según su cuenta. "
            "Escriba EJECUTAR para continuar: "
        ).strip()
        if confirmacion != "EJECUTAR":
            print("Ejecución cancelada.")
            return
    else:
        print("Opción no válida.")
        return
    subprocess.run(comando, cwd=RAIZ, check=False)


def mostrar_menu():
    print("\n" + "=" * 62)
    print(" TEO - GRAMÁTICAS FORMALES Y LENGUAJE NATURAL")
    print("=" * 62)
    print("1. Analizar código mini-C")
    print("2. Analizar una oración con la gramática reducida del español")
    print("3. Ejecutar pruebas del parser mini-C")
    print("4. Ejecutar demo exploratoria de spaCy")
    print("5. Evaluar el parser propio con las 60 oraciones")
    print("6. Preparar o ejecutar el experimento LLM")
    print("0. Salir")


def menu():
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "0":
            print("Hasta luego.")
            return
        if opcion == "1":
            codigo = leer_codigo_multilinea()
            if codigo is not None:
                procesar(codigo, dibujar=True)
        elif opcion == "2":
            oracion = input("Escriba la oración: ").strip()
            if oracion:
                procesar_espanol(oracion)
            else:
                print("No se ingresó ninguna oración.")
        elif opcion == "3":
            ejecutar_pruebas_minic()
        elif opcion == "4":
            ejecutar_demo_spacy()
        elif opcion == "5":
            evaluar_corpus_espanol()
        elif opcion == "6":
            ejecutar_experimento_llm()
        else:
            print("Opción no válida. Intente de nuevo.")
        input("\nPresione Enter para volver al menú...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1]).expanduser()
        try:
            entrada = ruta.read_text(encoding="utf-8")
        except OSError as error:
            print(f"No se pudo leer el archivo '{ruta}': {error}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0 if procesar(entrada, dibujar=True) else 1)
    menu()
