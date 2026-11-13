"""Pruebas del experimento sin credenciales, red ni consumo de la API."""

import contextlib
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from espanol.parser_es import analizar_oracion
from llm import experimento as exp
from llm.prompts import EJEMPLOS, construir_prompts


def respuesta_api(decision="aceptar"):
    return {
        "id": "resp_prueba", "model": "modelo-prueba", "status": "completed",
        "usage": {"input_tokens": 100, "output_tokens": 30},
        "output": [{"type": "message", "content": [{
            "type": "output_text", "text": json.dumps({
                "decision": decision, "regla": "<oracion>", "explicacion": "Prueba controlada."
            }),
        }]}],
    }


class PruebasPrompts(unittest.TestCase):
    def test_ejemplos_fuera_del_corpus_y_coherentes_con_parser(self):
        corpus = exp.leer_corpus(exp.RAIZ / "pruebas" / "oraciones.csv")
        oraciones = {f["oracion"].casefold() for f in corpus}
        self.assertEqual(len(corpus), 60)
        for ejemplo in EJEMPLOS:
            self.assertNotIn(ejemplo["oracion"].casefold(), oraciones)
            aceptada, _, _ = analizar_oracion(ejemplo["oracion"])
            self.assertEqual(aceptada, ejemplo["respuesta"]["decision"] == "aceptar")

    def test_solo_few_shot_contiene_ejemplos(self):
        prompts = construir_prompts()
        self.assertTrue(prompts["few-shot"].startswith(prompts["zero-shot"]))
        self.assertNotIn("EJEMPLOS RESUELTOS", prompts["zero-shot"])
        self.assertIn("EJEMPLOS RESUELTOS", prompts["few-shot"])

    def test_peticion_no_filtra_etiquetas_y_usa_esquema(self):
        peticion = exp.crear_peticion("modelo", "reglas", "El niño lee.", 2000)
        self.assertEqual(peticion["input"][1]["content"],
                         'Analiza la oración de este objeto JSON:\n{"oracion": "El niño lee."}')
        self.assertNotIn("esperado_corpus", json.dumps(peticion))
        self.assertFalse(peticion["store"])
        self.assertTrue(peticion["text"]["format"]["strict"])


class PruebasEvaluacion(unittest.TestCase):
    def test_distingue_acierto_corpus_y_adhesion(self):
        metricas = exp.evaluar({"esperado": "aceptar"}, "aceptar", "rechazar")
        self.assertEqual(metricas, {
            "acerto_corpus": "si", "respeto_reglas": "no",
            "indicio_conocimiento_general": "si",
        })
        metricas = exp.evaluar({"esperado": "aceptar"}, "rechazar", "rechazar")
        self.assertEqual(metricas["acerto_corpus"], "no")
        self.assertEqual(metricas["respeto_reglas"], "si")
        self.assertEqual(metricas["indicio_conocimiento_general"], "no")

    def test_respuesta_valida(self):
        self.assertEqual(exp.extraer_clasificacion(respuesta_api())["decision"], "aceptar")

    def test_errores_no_son_rechazos_gramaticales(self):
        invalida = respuesta_api()
        invalida["output"][0]["content"][0]["text"] = '{"decision": "aceptar"}'
        refusal = respuesta_api()
        refusal["output"][0]["content"] = [{"type": "refusal", "refusal": "No."}]
        for respuesta in [invalida, refusal, {"status": "incomplete"}, {}, [],
                          {"status": "completed", "output": None},
                          {"status": "completed", "output": [None]}]:
            with self.subTest(respuesta=respuesta), self.assertRaises(ValueError):
                exp.extraer_clasificacion(respuesta)

    def test_corpus_con_id_duplicado_se_rechaza(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "corpus.csv"
            ruta.write_text("id,oracion,nivel,esperado,fenomeno\n"
                            "1,El niño lee.,3,aceptar,objeto\n"
                            "1,El niño lee.,3,aceptar,objeto\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                exp.leer_corpus(ruta)


class PruebasExperimento(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.salida = Path(self.temporal.name)
        self.entorno = patch.dict(os.environ, {
            "OPENAI_API_KEY": "clave-secreta-de-prueba", "OPENAI_MODEL": "modelo-prueba"
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)

    def ejecutar(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return exp.main(["--salida", str(self.salida), "--pausa", "0", *extra])

    def filas(self):
        with (self.salida / "resultados_llm.csv").open(encoding="utf-8", newline="") as archivo:
            return list(csv.DictReader(archivo))

    def test_preparar_genera_120_pendientes_sin_api(self):
        with patch.object(exp, "consultar_openai") as api:
            self.assertEqual(self.ejecutar("--preparar"), 0)
            api.assert_not_called()
        filas = self.filas()
        self.assertEqual(len(filas), 120)
        self.assertTrue(all(f["estado"] == "pendiente" for f in filas))
        self.assertTrue(all(f["acerto_corpus"] == "" for f in filas))
        self.assertTrue(all(f["decision_llm"] == "" for f in filas))
        self.assertEqual((self.salida / "logs.txt").read_text(encoding="utf-8"), "")

    def test_ejecucion_real_simulada_y_reanudacion_sin_duplicados(self):
        with patch.object(exp, "consultar_openai", return_value=respuesta_api()) as api:
            self.assertEqual(self.ejecutar("--limite", "2"), 0)
            self.assertEqual(api.call_count, 4)
            self.assertEqual(self.ejecutar("--limite", "2"), 0)
            self.assertEqual(api.call_count, 4)
        filas = self.filas()
        self.assertEqual(len(filas), 4)
        self.assertTrue(all(f["estado"] == "ok" for f in filas))
        self.assertTrue(all(f["acerto_corpus"] == "si" for f in filas))
        self.assertTrue(all(f["tokens_entrada"] == "100" for f in filas))
        log = (self.salida / "logs.txt").read_text(encoding="utf-8")
        self.assertEqual(len(log.splitlines()), 4)
        self.assertNotIn("clave-secreta-de-prueba", log)

    def test_error_preserva_respuesta_y_reanuda_caso_pendiente(self):
        incompleta = respuesta_api()
        incompleta["status"] = "incomplete"
        with patch.object(exp, "consultar_openai", side_effect=[respuesta_api(), incompleta]):
            self.assertEqual(self.ejecutar("--limite", "2"), 1)
        filas = self.filas()
        self.assertEqual([f["estado"] for f in filas], ["ok", "error", "pendiente", "pendiente"])
        self.assertEqual(filas[1]["acerto_corpus"], "")
        log = exp.leer_registros(self.salida / "logs.txt")
        self.assertEqual(log[1]["respuesta_api"]["status"], "incomplete")
        with patch.object(exp, "consultar_openai", return_value=respuesta_api()) as api:
            self.assertEqual(self.ejecutar("--limite", "2"), 0)
            self.assertEqual(api.call_count, 3)
        self.assertTrue(all(f["estado"] == "ok" for f in self.filas()))

    def test_no_mezcla_modelos_en_log_existente(self):
        with patch.object(exp, "consultar_openai", return_value=respuesta_api()):
            self.assertEqual(self.ejecutar("--limite", "1"), 0)
        anterior = (self.salida / "logs.txt").read_bytes()
        with patch.object(exp, "consultar_openai") as api:
            self.assertEqual(self.ejecutar("--limite", "1", "--modelo", "otro-modelo"), 1)
            api.assert_not_called()
        self.assertEqual((self.salida / "logs.txt").read_bytes(), anterior)

    def test_log_truncado_impide_repetir_solicitudes_silenciosamente(self):
        (self.salida / "logs.txt").write_text('{"id":', encoding="utf-8")
        with patch.object(exp, "consultar_openai") as api:
            self.assertEqual(self.ejecutar("--limite", "1"), 1)
            api.assert_not_called()

    def test_error_con_clave_se_oculta_y_detiene_ejecucion(self):
        with patch.object(exp, "consultar_openai", side_effect=RuntimeError("clave-secreta-de-prueba")):
            self.assertEqual(self.ejecutar("--limite", "1"), 1)
        self.assertNotIn(
            "clave-secreta-de-prueba",
            (self.salida / "logs.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(self.filas()[0]["estado"], "error")

    def test_respuesta_con_formato_invalido_se_guarda_como_error(self):
        with patch.object(exp, "consultar_openai", return_value=["respuesta inválida"]):
            self.assertEqual(self.ejecutar("--limite", "1"), 1)
        self.assertEqual(self.filas()[0]["estado"], "error")
        self.assertEqual(self.filas()[0]["decision_llm"], "")
        self.assertEqual(exp.leer_registros(self.salida / "logs.txt")[0]["respuesta_api"],
                         ["respuesta inválida"])

    def test_sin_clave_no_hace_peticiones(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}), patch.object(exp, "consultar_openai") as api:
            self.assertEqual(self.ejecutar("--limite", "1"), 1)
            api.assert_not_called()
        self.assertFalse((self.salida / "logs.txt").exists())

    def test_conserva_revision_manual_al_reanudar(self):
        with patch.object(exp, "consultar_openai", return_value=respuesta_api()):
            self.assertEqual(self.ejecutar("--limite", "1"), 0)
        filas = self.filas()
        filas[0]["revision_manual"] = "Decisión revisada por el equipo."
        with (self.salida / "resultados_llm.csv").open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=exp.CAMPOS)
            escritor.writeheader()
            escritor.writerows(filas)
        with patch.object(exp, "consultar_openai") as api:
            self.assertEqual(self.ejecutar("--limite", "1"), 0)
            api.assert_not_called()
        self.assertEqual(self.filas()[0]["revision_manual"], "Decisión revisada por el equipo.")

    def test_env_no_sobrescribe_variables_ni_ejecuta_codigo(self):
        ruta = self.salida / ".env"
        ruta.write_text('OPENAI_MODEL="otro-modelo"\nIGNORAR=$(comando)\n', encoding="utf-8")
        exp.cargar_entorno(ruta)
        self.assertEqual(os.environ["OPENAI_MODEL"], "modelo-prueba")
        self.assertNotIn("IGNORAR", os.environ)

    def test_transporte_http_y_timeout_no_exponen_credenciales(self):
        fallas = [HTTPError(exp.ENDPOINT, 401, "Unauthorized", {}, None),
                  URLError("clave-secreta-de-prueba"), TimeoutError()]
        for falla in fallas:
            with self.subTest(falla=type(falla)), patch.object(
                exp.request, "urlopen", side_effect=falla
            ), self.assertRaises(RuntimeError) as capturada:
                exp.consultar_openai({}, "clave-secreta-de-prueba", 10)
            self.assertNotIn("clave-secreta-de-prueba", str(capturada.exception))


if __name__ == "__main__":
    unittest.main()
