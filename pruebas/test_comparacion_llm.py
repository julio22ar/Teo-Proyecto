"""Comparación reproducible con respuestas sintéticas solo en archivos temporales."""

import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from espanol.parser_es import analizar_oracion
from llm import comparar
from llm.experimento import guardar_resultados, huella, leer_corpus
from llm.prompts import MODOS, RAIZ


class PruebasComparacionLLM(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.salida = Path(self.temporal.name)
        self.corpus = leer_corpus(RAIZ / "pruebas" / "oraciones.csv")
        self.configuracion = {
            "modos": list(MODOS), "modelo": "modelo-de-prueba",
            "corpus": self.corpus,
            "parser_sha256": hashlib.sha256((RAIZ / "espanol" / "parser_es.py").read_bytes()).hexdigest(),
        }
        self.firma = huella(self.configuracion)
        self.registros = []
        for modo in MODOS:
            for caso in self.corpus:
                acepta, _, _ = analizar_oracion(caso["oracion"])
                # Zero-shot sigue el corpus, few-shot sigue la CFG: permite
                # comprobar que las dos métricas no se confunden.
                decision = caso["esperado"] if modo == "zero-shot" else "aceptar" if acepta else "rechazar"
                clasificacion = {"decision": decision, "regla": "regla de prueba",
                                 "explicacion": "Respuesta sintética, no una medición real."}
                self.registros.append({
                    "id": caso["id"], "modo": modo, "huella": self.firma, "estado": "ok",
                    "fecha_utc": "2026-11-17T18:00:00+00:00", "clasificacion": clasificacion,
                    "respuesta_api": {
                        "id": f"resp_prueba_{modo}_{caso['id']}", "model": "modelo-de-prueba",
                        "status": "completed", "usage": {"input_tokens": 10, "output_tokens": 5},
                        "output": [{"type": "message", "content": [{"type": "output_text",
                                                                     "text": json.dumps(clasificacion)}]}],
                    },
                })
        self.guardar()
        self.informe = self.salida / "informe.md"
        self.informe.write_text(
            "Texto del equipo.\n<!-- LLM_ESTADO_INICIO -->\nPendiente.\n<!-- LLM_ESTADO_FIN -->\n"
            "Sección ajena al LLM.\n<!-- LLM_RESULTADOS_INICIO -->\nTabla pendiente.\n"
            "<!-- LLM_RESULTADOS_FIN -->\nTexto final del equipo.\n", encoding="utf-8"
        )

    def guardar(self):
        (self.salida / "configuracion.json").write_text(
            json.dumps(dict(self.configuracion, huella=self.firma)), encoding="utf-8"
        )
        (self.salida / "logs.txt").write_text(
            "\n".join(json.dumps(r) for r in self.registros) + "\n", encoding="utf-8"
        )
        guardar_resultados(self.salida, self.corpus, MODOS, self.registros, "modelo-de-prueba")

    def ejecutar(self, *opciones):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return comparar.main(["--salida", str(self.salida), "--informe", str(self.informe), *opciones])

    def test_compara_decisiones_con_referencias_distintas(self):
        filas, configuracion = comparar.cargar_resultados(self.salida)
        resumen = comparar.resumir(filas)
        zero, few = (resumen["por_modo"][modo] for modo in MODOS)
        self.assertEqual(zero["aciertos_corpus"], 60)
        self.assertEqual(zero["respetan_reglas"], 46)
        self.assertEqual(zero["indicios"], 14)
        self.assertEqual(few["aciertos_corpus"], 46)
        self.assertEqual(few["respetan_reglas"], 60)
        self.assertEqual(few["indicios"], 0)
        self.assertEqual(resumen["pares_adhesion"]["solo_few_shot"], 14)
        self.assertEqual(resumen["pares_adhesion"]["ambos_respetan"], 46)
        self.assertEqual(len(resumen["cambios"]), 14)
        self.assertEqual(zero["tokens_entrada"], 600)
        self.assertEqual(few["tokens_salida"], 300)
        self.assertEqual(resumen["por_nivel"]["3"]["zero-shot"]["respetan_reglas"], 6)

    def test_actualiza_solo_bloques_llm_y_es_repetible(self):
        self.assertEqual(self.ejecutar("--actualizar-informe"), 0)
        informe = self.informe.read_text(encoding="utf-8")
        self.assertIn("Texto del equipo.", informe)
        self.assertIn("Sección ajena al LLM.", informe)
        self.assertIn("Texto final del equipo.", informe)
        self.assertIn("+23.33 puntos", informe)
        self.assertIn("100.00%", informe)
        self.assertIn("17/11/2026 12:00", informe)
        self.assertNotIn("Tabla pendiente", informe)
        self.assertEqual(self.ejecutar("--actualizar-informe"), 0)
        self.assertEqual(informe, self.informe.read_text(encoding="utf-8"))

    def test_consulta_no_modifica_el_informe(self):
        anterior = self.informe.read_bytes()
        self.assertEqual(self.ejecutar(), 0)
        self.assertEqual(self.informe.read_bytes(), anterior)
        self.assertTrue((self.salida / "comparacion.json").is_file())

    def test_salida_en_windows_cp1252_no_falla_despues_de_escribir(self):
        buffer = io.BytesIO()
        consola = io.TextIOWrapper(buffer, encoding="cp1252")
        with contextlib.redirect_stdout(consola), contextlib.redirect_stderr(io.StringIO()):
            resultado = comparar.main(["--salida", str(self.salida)])
        consola.flush()
        self.assertEqual(resultado, 0)
        self.assertIn(b"UTC-6", buffer.getvalue())

    def test_incompleto_no_genera_cifras_ni_modifica_informe(self):
        self.registros.pop()
        self.guardar()
        anterior = self.informe.read_bytes()
        self.assertEqual(self.ejecutar("--actualizar-informe"), 1)
        self.assertEqual(self.informe.read_bytes(), anterior)
        self.assertFalse((self.salida / "comparacion.json").exists())

    def test_csv_manipulado_no_se_presenta_como_resultado(self):
        ruta = self.salida / "resultados_llm.csv"
        with ruta.open(encoding="utf-8", newline="") as archivo:
            lector = csv.DictReader(archivo)
            campos = lector.fieldnames
            filas = list(lector)
        filas[0]["decision_llm"] = "rechazar"
        with ruta.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(filas)
        anterior = self.informe.read_bytes()
        self.assertEqual(self.ejecutar("--actualizar-informe"), 1)
        self.assertEqual(self.informe.read_bytes(), anterior)

    def test_sin_log_no_se_actualiza_informe(self):
        (self.salida / "logs.txt").write_text("", encoding="utf-8")
        self.assertEqual(self.ejecutar("--actualizar-informe"), 1)

    def test_huella_incorrecta_se_rechaza(self):
        self.configuracion["modelo"] = "modelo-distinto"
        self.guardar()
        self.assertEqual(self.ejecutar("--actualizar-informe"), 1)

    def test_informe_sin_marcadores_se_conserva(self):
        self.informe.write_text("Informe del equipo sin marcadores.\n", encoding="utf-8")
        anterior = self.informe.read_bytes()
        self.assertEqual(self.ejecutar("--actualizar-informe"), 1)
        self.assertEqual(self.informe.read_bytes(), anterior)
        self.assertFalse((self.salida / "comparacion.json").exists())


if __name__ == "__main__":
    unittest.main()
