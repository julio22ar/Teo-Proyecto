"""Compara la corrida completa y actualiza el informe con resultados registrados.

    python -m llm.comparar
    python -m llm.comparar --actualizar-informe

No consulta la API. Exige una corrida completa y coherente con sus registros.
"""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import sys

from espanol.parser_es import analizar_oracion
from llm.experimento import evaluar, extraer_clasificacion, huella, leer_registros
from llm.prompts import MODOS, RAIZ


ZONA_LOCAL = timezone(timedelta(hours=-6), "America/El_Salvador")


def cargar_resultados(salida):
    """Coteja CSV, configuración y respuestas originales antes de informar cifras."""
    configuracion = json.loads((salida / "configuracion.json").read_text(encoding="utf-8"))
    firma = configuracion.pop("huella")
    if huella(configuracion) != firma:
        raise ValueError("La huella de la configuración no coincide con su contenido.")
    if set(configuracion["modos"]) != set(MODOS):
        raise ValueError("La comparación requiere zero-shot y few-shot en la misma corrida.")
    corpus = {fila["id"]: fila for fila in configuracion["corpus"]}
    if len(corpus) != 60:
        raise ValueError("El informe requiere el experimento completo de 60 oraciones.")
    if hashlib.sha256((RAIZ / "espanol" / "parser_es.py").read_bytes()).hexdigest() != configuracion["parser_sha256"]:
        raise ValueError("El parser cambió desde la corrida. Revisa las referencias antes de comparar.")
    with (salida / "resultados_llm.csv").open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    esperadas = {(ident, modo) for ident in corpus for modo in MODOS}
    obtenidas = {(f["id"], f["modo"]) for f in filas}
    if len(filas) != len(esperadas) or obtenidas != esperadas:
        raise ValueError("El CSV debe contener una fila por oración y modo: 120 filas sin duplicados.")
    completadas = sum(f["estado"] == "ok" for f in filas)
    if completadas != 120:
        raise ValueError(f"Corrida incompleta: {completadas}/120 respuestas ok. El informe se conserva.")
    registros = leer_registros(salida / "logs.txt")
    if any(r["huella"] != firma for r in registros):
        raise ValueError("El log contiene intentos de otra configuración.")
    ultimos = {(r["id"], r["modo"]): r for r in registros}
    for fila in filas:
        referencia = corpus[fila["id"]]
        aceptada, _, _ = analizar_oracion(referencia["oracion"])
        esperado_cfg = "aceptar" if aceptada else "rechazar"
        if any(fila[campo] != referencia[campo] for campo in ("oracion", "nivel", "fenomeno")) or (
            fila["esperado_corpus"] != referencia["esperado"] or fila["esperado_cfg"] != esperado_cfg
        ):
            raise ValueError("Las referencias del CSV no coinciden con el corpus de la corrida.")
        registro = ultimos.get((fila["id"], fila["modo"]), {})
        if registro.get("estado") != "ok":
            raise ValueError("Falta una respuesta ok en el log para una fila del CSV.")
        respuesta = registro["respuesta_api"]
        clasificacion = extraer_clasificacion(respuesta)
        if any(fila[campo_csv] != clasificacion[campo_json] for campo_csv, campo_json in (
            ("decision_llm", "decision"), ("regla_llm", "regla"), ("explicacion_llm", "explicacion")
        )):
            raise ValueError("El CSV no coincide con el texto de la respuesta guardada.")
        if (not respuesta.get("id") or fila["response_id"] != respuesta["id"] or
                fila["modelo_respuesta"] != respuesta.get("model") or
                fila["modelo_solicitado"] != configuracion["modelo"] or
                fila["fecha_utc"] != registro["fecha_utc"]):
            raise ValueError("Los identificadores, modelo o fecha no coinciden con la corrida.")
        metricas = evaluar(referencia, clasificacion["decision"], esperado_cfg)
        if any(fila[campo] != valor for campo, valor in metricas.items()):
            raise ValueError("Las métricas del CSV fueron alteradas o están desactualizadas.")
    return filas, configuracion


def contar(filas):
    total = len(filas)
    aciertos = sum(f["acerto_corpus"] == "si" for f in filas)
    adhesion = sum(f["respeto_reglas"] == "si" for f in filas)
    return {
        "total": total, "aciertos_corpus": aciertos, "respetan_reglas": adhesion,
        "exactitud_corpus": aciertos / total, "adhesion_cfg": adhesion / total,
        "indicios": sum(f["indicio_conocimiento_general"] == "si" for f in filas),
        "revisiones_manuales": sum(bool(f["revision_manual"].strip()) for f in filas),
        "tokens_entrada": sum(int(f["tokens_entrada"] or 0) for f in filas),
        "tokens_salida": sum(int(f["tokens_salida"] or 0) for f in filas),
    }


def resumir(filas):
    modos = {modo: contar([f for f in filas if f["modo"] == modo]) for modo in MODOS}
    niveles = {
        nivel: {modo: contar([f for f in filas if f["modo"] == modo and f["nivel"] == nivel])
                for modo in MODOS}
        for nivel in sorted({f["nivel"] for f in filas})
    }
    por_id = {modo: {f["id"]: f for f in filas if f["modo"] == modo} for modo in MODOS}
    cambios = []
    pares = {"ambos_respetan": 0, "solo_few_shot": 0, "solo_zero_shot": 0, "ninguno_respeta": 0}
    for ident, zero in por_id["zero-shot"].items():
        few = por_id["few-shot"][ident]
        cumple_zero, cumple_few = zero["respeto_reglas"] == "si", few["respeto_reglas"] == "si"
        nombre = ("ambos_respetan" if cumple_zero and cumple_few else "solo_few_shot"
                  if cumple_few else "solo_zero_shot" if cumple_zero else "ninguno_respeta")
        pares[nombre] += 1
        if zero["decision_llm"] != few["decision_llm"]:
            cambios.append({
                "id": ident, "oracion": zero["oracion"], "esperado_cfg": zero["esperado_cfg"],
                "zero_shot": zero["decision_llm"], "few_shot": few["decision_llm"],
            })
    return {"por_modo": modos, "por_nivel": niveles, "pares_adhesion": pares, "cambios": cambios}


def celda(valor):
    return escape(str(valor)).replace("|", "\\|").replace("\n", " ")


def fecha_local(valor):
    fecha = datetime.fromisoformat(valor)
    if fecha.tzinfo is None:
        raise ValueError("La fecha de una respuesta no tiene zona horaria.")
    return fecha.astimezone(ZONA_LOCAL).strftime("%d/%m/%Y %H:%M")


def generar_markdown(filas, resumen, modelo):
    lineas = [
        "### Comparación zero-shot y few-shot", "",
        f"Modelo solicitado: `{celda(modelo)}`. Corrida completa: **120/120 respuestas ok**.",
        "Las fechas siguientes corresponden a America/El_Salvador (UTC-6).", "",
        "| Modo | Modelo devuelto y fecha | Completados/60 | Errores finales | Exactitud corpus | Adhesión CFG | Indicios |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for modo in MODOS:
        datos = resumen["por_modo"][modo]
        grupo = [f for f in filas if f["modo"] == modo]
        modelos = ", ".join(sorted({f["modelo_respuesta"] for f in grupo}))
        fechas = sorted(f["fecha_utc"] for f in grupo)
        lineas.append(
            f"| {modo} | {celda(modelos)}; {fecha_local(fechas[0])} a {fecha_local(fechas[-1])} | "
            f"60/60 | 0 | {datos['aciertos_corpus']}/60 ({datos['exactitud_corpus']:.2%}) | "
            f"{datos['respetan_reglas']}/60 ({datos['adhesion_cfg']:.2%}) | {datos['indicios']} |"
        )
    zero, few = (resumen["por_modo"][modo] for modo in MODOS)
    diferencia = 100 * (few["adhesion_cfg"] - zero["adhesion_cfg"])
    diferencia_corpus = 100 * (few["exactitud_corpus"] - zero["exactitud_corpus"])
    lineas += [
        "", f"El cambio de few-shot respecto a zero-shot es **{diferencia:+.2f} puntos "
        f"porcentuales en adhesión** y **{diferencia_corpus:+.2f} en exactitud del corpus**.",
        "La adhesión es la métrica que responde directamente a la consigna de aplicar "
        "la gramática reducida. Una exactitud mayor en el corpus puede provenir de aceptar "
        "construcciones del español general fuera del subconjunto.", "",
        "| Nivel del corpus | Modo | Aciertos corpus | Respeta CFG | Indicios |",
        "| --- | --- | --- | --- | --- |",
    ]
    for nivel, modos in resumen["por_nivel"].items():
        for modo, datos in modos.items():
            lineas.append(f"| {celda(nivel)} | {modo} | {datos['aciertos_corpus']}/{datos['total']} | "
                          f"{datos['respetan_reglas']}/{datos['total']} | {datos['indicios']} |")
    pares = resumen["pares_adhesion"]
    lineas += [
        "", "| Comparación sobre las mismas 60 oraciones | Cantidad |", "| --- | --- |",
        f"| Ambos modos respetan la CFG | {pares['ambos_respetan']} |",
        f"| Solo few-shot respeta la CFG | {pares['solo_few_shot']} |",
        f"| Solo zero-shot respeta la CFG | {pares['solo_zero_shot']} |",
        f"| Ninguno respeta la CFG | {pares['ninguno_respeta']} |", "",
        "| Modo | Tokens de entrada | Tokens de salida | Explicaciones con revisión anotada |",
        "| --- | --- | --- | --- |",
    ]
    for modo, datos in resumen["por_modo"].items():
        lineas.append(f"| {modo} | {datos['tokens_entrada']} | {datos['tokens_salida']} | "
                      f"{datos['revisiones_manuales']}/60 |")
    lineas += ["", "Los tokens de esta tabla corresponden a las respuestas finales ok; no incluyen "
               "intentos previos fallidos ni constituyen una factura. Un indicio no demuestra el "
               "proceso interno del modelo. La coincidencia de decisión tampoco valida la explicación: "
               "su revisión se anota en `revision_manual` del CSV.", ""]
    if resumen["cambios"]:
        lineas += ["#### Oraciones cuya decisión cambia", "",
                   "| ID | Oración | Referencia CFG | Zero-shot | Few-shot |",
                   "| --- | --- | --- | --- | --- |"]
        for cambio in resumen["cambios"]:
            lineas.append("| " + " | ".join(celda(cambio[campo]) for campo in (
                "id", "oracion", "esperado_cfg", "zero_shot", "few_shot"
            )) + " |")
    else:
        lineas.append("Ambos modos emitieron la misma decisión en las 60 oraciones.")
    lineas += ["", "Son resultados descriptivos de una corrida de este corpus; no demuestran "
               "superioridad general de un modo ni la clase formal de todo el español."]
    return "\n".join(lineas)


def sustituir_bloque(texto, nombre, contenido):
    inicio, fin = f"<!-- {nombre}_INICIO -->", f"<!-- {nombre}_FIN -->"
    if texto.count(inicio) != 1 or texto.count(fin) != 1:
        raise ValueError(f"El informe debe contener un único bloque {nombre}.")
    antes, resto = texto.split(inicio)
    _, despues = resto.split(fin)
    return antes + inicio + "\n" + contenido + "\n" + fin + despues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=RAIZ / "llm")
    parser.add_argument("--actualizar-informe", action="store_true")
    parser.add_argument("--informe", type=Path, default=RAIZ / "informe" / "informe.md")
    args = parser.parse_args(argv)
    try:
        filas, configuracion = cargar_resultados(args.salida)
        resumen = resumir(filas)
        markdown = generar_markdown(filas, resumen, configuracion["modelo"])
        informe = None
        if args.actualizar_informe:
            informe = args.informe.read_text(encoding="utf-8")
            informe = sustituir_bloque(informe, "LLM_RESULTADOS", markdown)
            informe = sustituir_bloque(informe, "LLM_ESTADO",
                                      "El experimento LLM está completado: 120 respuestas reales "
                                      "registradas; los resultados se presentan en la sección 7.")
        # Validar todo antes de escribir cualquier archivo de comparación.
        (args.salida / "comparacion.json").write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (args.salida / "comparacion.md").write_text(markdown + "\n", encoding="utf-8")
        if informe is not None:
            args.informe.write_text(informe, encoding="utf-8")
        print(markdown)
        if informe is not None:
            print(f"\nInforme actualizado: {args.informe}")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("No se pudo comparar: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
