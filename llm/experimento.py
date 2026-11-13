import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from urllib import error, request

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from espanol.parser_es import analizar_oracion
from llm.prompts import ESQUEMA_RESPUESTA, MODOS, RAIZ, construir_prompts, mensaje_oracion


ENDPOINT = "https://api.openai.com/v1/responses"
CAMPOS = (
    "id", "oracion", "nivel", "fenomeno", "modo", "esperado_corpus", "esperado_cfg",
    "motivo_cfg", "estado", "decision_llm", "acerto_corpus", "respeto_reglas",
    "indicio_conocimiento_general", "regla_llm", "explicacion_llm", "revision_manual",
    "modelo_solicitado", "modelo_respuesta", "response_id", "fecha_utc",
    "tokens_entrada", "tokens_salida", "error",
)


def cargar_entorno(ruta):
    if not ruta.exists():
        return
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8-sig").splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        clave, separador, valor = linea.partition("=")
        if not separador:
            raise ValueError(f"Línea {numero} de .env: se esperaba NOMBRE=valor.")
        clave, valor = clave.strip(), valor.strip()
        if clave not in ("OPENAI_API_KEY", "OPENAI_MODEL"):
            continue
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        os.environ.setdefault(clave, valor)


def leer_corpus(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        requeridos = {"id", "oracion", "nivel", "esperado", "fenomeno"}
        if not requeridos.issubset(lector.fieldnames or []):
            raise ValueError("El corpus no tiene todas las columnas requeridas.")
        filas = list(lector)
    ids = set()
    for fila in filas:
        if not fila["id"] or fila["id"] in ids:
            raise ValueError("Los identificadores del corpus deben ser únicos y no vacíos.")
        ids.add(fila["id"])
        if not fila["oracion"].strip() or fila["esperado"] not in ("aceptar", "rechazar"):
            raise ValueError(f"Oración o etiqueta inválida en el caso {fila['id']}.")
    if not filas:
        raise ValueError("El corpus está vacío.")
    return filas


def huella(valor):
    return hashlib.sha256(json.dumps(
        valor, ensure_ascii=False, sort_keys=True
    ).encode("utf-8")).hexdigest()


def crear_peticion(modelo, prompt, oracion, max_tokens):
    return {
        "model": modelo,
        "store": False,
        "input": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": mensaje_oracion(oracion)},
        ],
        "max_output_tokens": max_tokens,
        "text": {"format": {
            "type": "json_schema", "name": "clasificacion_gramatical",
            "strict": True, "schema": ESQUEMA_RESPUESTA,
        }},
    }


def consultar_openai(peticion, clave, timeout):
    req = request.Request(
        ENDPOINT, data=json.dumps(peticion, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + clave, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as respuesta:
            return json.load(respuesta)
    except error.HTTPError as exc:
        raise RuntimeError(
            f"OpenAI HTTP {exc.code}. Comprueba modelo, permisos, cuota y formato "
            "según el código HTTP; la ejecución se puede reanudar."
        ) from None
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Fallo de conexión o tiempo de espera. La API podría haber procesado la "
            "solicitud; revisa el uso antes de repetirla."
        ) from None


def extraer_clasificacion(respuesta):
    if not isinstance(respuesta, dict) or respuesta.get("status") != "completed":
        raise ValueError("La API no devolvió una respuesta completada.")
    partes = []
    salida = respuesta.get("output")
    if not isinstance(salida, list):
        raise ValueError("La respuesta no contiene una lista de elementos de salida.")
    for item in salida:
        if not isinstance(item, dict):
            raise ValueError("Un elemento de la salida tiene formato inválido.")
        if item.get("type") != "message":
            continue
        contenidos = item.get("content")
        if not isinstance(contenidos, list):
            raise ValueError("El mensaje no contiene una lista de contenidos.")
        for contenido in contenidos:
            if not isinstance(contenido, dict):
                raise ValueError("Un contenido del mensaje tiene formato inválido.")
            if contenido.get("type") == "refusal":
                raise ValueError("El modelo rechazó responder; no es un rechazo gramatical.")
            if contenido.get("type") == "output_text":
                if not isinstance(contenido.get("text"), str):
                    raise ValueError("El texto de la respuesta tiene formato inválido.")
                partes.append(contenido["text"])
    try:
        resultado = json.loads("".join(partes))
    except (json.JSONDecodeError, TypeError):
        raise ValueError("La respuesta no contiene un objeto JSON válido.") from None
    if not isinstance(resultado, dict) or set(resultado) != set(ESQUEMA_RESPUESTA["required"]):
        raise ValueError("La respuesta no tiene los tres campos requeridos.")
    if resultado["decision"] not in ("aceptar", "rechazar") or any(
        not isinstance(resultado[campo], str) or not resultado[campo].strip()
        for campo in ("regla", "explicacion")
    ):
        raise ValueError("La decisión, regla o explicación tiene un valor inválido.")
    return resultado


def evaluar(fila, decision, esperado_cfg):
    return {
        "acerto_corpus": "si" if decision == fila["esperado"] else "no",
        "respeto_reglas": "si" if decision == esperado_cfg else "no",
        "indicio_conocimiento_general": "si" if (
            esperado_cfg != fila["esperado"] and decision == fila["esperado"]
        ) else "no",
    }


def leer_registros(ruta):
    if not ruta.exists():
        return []
    registros = []
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        try:
            registro = json.loads(linea)
        except json.JSONDecodeError:
            raise ValueError(
                f"Log incompleto en línea {numero}. Conserva una copia y repara esa "
                "línea antes de reanudar; no se ignorarán respuestas anteriores."
            ) from None
        if not isinstance(registro, dict) or not {"id", "modo", "estado", "huella"}.issubset(registro):
            raise ValueError(f"Registro de log inválido en línea {numero}.")
        registros.append(registro)
    return registros


def guardar_resultados(salida, filas, modos, registros, modelo):
    ultimos = {(r["id"], r["modo"]): r for r in registros}
    revisiones = {}
    destino = salida / "resultados_llm.csv"
    if destino.exists():
        with destino.open(encoding="utf-8", newline="") as archivo:
            for anterior in csv.DictReader(archivo):
                revisiones[(anterior["id"], anterior["modo"])] = anterior.get("revision_manual", "")
    resumen = {}
    temporal = destino.with_suffix(".csv.tmp")
    with temporal.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
        escritor.writeheader()
        for modo in modos:
            contadores = {"total": len(filas), "completados": 0, "errores": 0,
                          "aciertos_corpus": 0, "respetan_reglas": 0, "indicios": 0}
            for fila in filas:
                aceptada, _, motivo = analizar_oracion(fila["oracion"])
                esperado_cfg = "aceptar" if aceptada else "rechazar"
                registro = ultimos.get((fila["id"], modo), {})
                datos = {campo: "" for campo in CAMPOS}
                datos.update({
                    "id": fila["id"], "oracion": fila["oracion"], "nivel": fila["nivel"],
                    "fenomeno": fila["fenomeno"], "modo": modo,
                    "esperado_corpus": fila["esperado"], "esperado_cfg": esperado_cfg,
                    "motivo_cfg": motivo or "", "estado": registro.get("estado", "pendiente"),
                    "modelo_solicitado": modelo,
                    "revision_manual": revisiones.get((fila["id"], modo), ""),
                })
                if registro:
                    respuesta = registro.get("respuesta_api")
                    respuesta = respuesta if isinstance(respuesta, dict) else {}
                    uso = respuesta.get("usage")
                    uso = uso if isinstance(uso, dict) else {}
                    datos.update({
                        "modelo_respuesta": respuesta.get("model", ""),
                        "response_id": respuesta.get("id", ""),
                        "fecha_utc": registro["fecha_utc"], "error": registro.get("error", ""),
                        "tokens_entrada": uso.get("input_tokens", ""),
                        "tokens_salida": uso.get("output_tokens", ""),
                    })
                if registro.get("estado") == "ok":
                    clasificacion = registro["clasificacion"]
                    metricas = evaluar(fila, clasificacion["decision"], esperado_cfg)
                    datos.update(metricas)
                    datos.update({"decision_llm": clasificacion["decision"],
                                  "regla_llm": clasificacion["regla"],
                                  "explicacion_llm": clasificacion["explicacion"]})
                    contadores["completados"] += 1
                    contadores["aciertos_corpus"] += metricas["acerto_corpus"] == "si"
                    contadores["respetan_reglas"] += metricas["respeto_reglas"] == "si"
                    contadores["indicios"] += metricas["indicio_conocimiento_general"] == "si"
                elif registro.get("estado") == "error":
                    contadores["errores"] += 1
                escritor.writerow(datos)
            n = contadores["completados"]
            contadores["exactitud_corpus"] = contadores["aciertos_corpus"] / n if n else None
            contadores["adhesion_cfg"] = contadores["respetan_reglas"] / n if n else None
            resumen[modo] = contadores
    temporal.replace(destino)
    (salida / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return resumen


def ejecutar(args):
    filas = leer_corpus(args.corpus)
    if args.limite:
        filas = filas[:args.limite]
    modos = MODOS if args.modo == "ambos" else (args.modo,)
    prompts = construir_prompts()
    modelo = args.modelo or os.environ.get("OPENAI_MODEL", "").strip()
    clave = os.environ.get("OPENAI_API_KEY", "").strip()
    if not args.preparar and (not clave or not modelo):
        raise ValueError("Configura OPENAI_API_KEY y OPENAI_MODEL en .env o el entorno "
                         "(o pasa --modelo). Usa --preparar para trabajar sin API.")
    configuracion = {
        "proveedor": "OpenAI", "endpoint": ENDPOINT, "modelo": modelo,
        "modos": modos, "corpus": filas, "prompts": prompts,
        "esquema": ESQUEMA_RESPUESTA, "max_output_tokens": args.max_tokens,
        "parser_sha256": hashlib.sha256(
            (RAIZ / "espanol" / "parser_es.py").read_bytes()
        ).hexdigest(),
    }
    firma = huella(configuracion)
    salida = args.salida
    salida.mkdir(parents=True, exist_ok=True)
    ruta_log = salida / "logs.txt"
    registros = leer_registros(ruta_log)
    if any(r["huella"] != firma for r in registros):
        raise ValueError("La configuración cambió respecto al log: modelo, corpus, modos, "
                         "prompts, parser o límite de tokens. Usa otro --salida.")
    manifiesto = dict(configuracion, huella=firma)
    (salida / "configuracion.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ruta_log.touch(exist_ok=True)
    completados = {(r["id"], r["modo"]) for r in registros if r["estado"] == "ok"}
    guardar_resultados(salida, filas, modos, registros, modelo)
    pendientes = len(filas) * len(modos) - len(completados)
    print(f"{len(filas)} oraciones; {len(modos)} modos; {pendientes} solicitudes pendientes.")
    if args.preparar:
        print(f"Preparación local en {salida}. No se consultó la API; no hay resultados medidos.")
        return 0
    for modo in modos:
        for fila in filas:
            if (fila["id"], modo) in completados:
                continue
            peticion = crear_peticion(modelo, prompts[modo], fila["oracion"], args.max_tokens)
            registro = {
                "id": fila["id"], "modo": modo, "huella": firma,
                "fecha_utc": datetime.now(timezone.utc).isoformat(),
                "peticion": peticion, "respuesta_api": None, "estado": "error",
            }
            try:
                respuesta = consultar_openai(peticion, clave, args.timeout)
                registro["respuesta_api"] = respuesta
                registro["clasificacion"] = extraer_clasificacion(respuesta)
                registro["estado"] = "ok"
            except (RuntimeError, ValueError, OSError) as exc:
                registro["error"] = str(exc).replace(clave, "[CLAVE OCULTA]")
            linea = json.dumps(registro, ensure_ascii=False).replace(clave, "[CLAVE OCULTA]")
            with ruta_log.open("a", encoding="utf-8") as archivo:
                archivo.write(linea + "\n")
            registros.append(json.loads(linea))
            guardar_resultados(salida, filas, modos, registros, modelo)
            print(f"{modo} | caso {fila['id']} | {registro['estado']}")
            if registro["estado"] == "error":
                print(registro["error"], file=sys.stderr)
                return 1
            if args.pausa:
                time.sleep(args.pausa)
    print(f"Experimento terminado. Resultados y respuestas completas en {salida}.")
    return 0


def numero_positivo(texto):
    numero = int(texto)
    if numero <= 0:
        raise argparse.ArgumentTypeError("Se requiere un entero mayor que cero.")
    return numero


def segundos_no_negativos(texto):
    numero = float(texto)
    if not 0 <= numero < float("inf"):
        raise argparse.ArgumentTypeError("Se requiere un número finito no negativo.")
    return numero


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparar", action="store_true", help="Generar archivos sin llamar a la API.")
    parser.add_argument("--modelo", help="Identificador de modelo; alternativa a OPENAI_MODEL.")
    parser.add_argument("--modo", choices=("ambos",) + MODOS, default="ambos")
    parser.add_argument("--corpus", type=Path, default=RAIZ / "pruebas" / "oraciones.csv")
    parser.add_argument("--salida", type=Path, default=RAIZ / "llm")
    parser.add_argument("--limite", type=numero_positivo, help="Primeras N oraciones; para un piloto.")
    parser.add_argument("--max-tokens", type=numero_positivo, default=2000)
    parser.add_argument("--timeout", type=numero_positivo, default=90)
    parser.add_argument("--pausa", type=segundos_no_negativos, default=0.5)
    args = parser.parse_args(argv)
    try:
        cargar_entorno(RAIZ / ".env")
        return ejecutar(args)
    except (ValueError, OSError, RecursionError) as exc:
        clave = os.environ.get("OPENAI_API_KEY", "")
        mensaje = str(exc)
        if clave:
            mensaje = mensaje.replace(clave, "[CLAVE OCULTA]")
        print("Error: " + mensaje, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrumpido. Los casos ya guardados se conservaron.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
