"""Pruebas del paso de código mini-C al módulo semántico y su opción de menú."""

import contextlib
import io
import sys
import types
import unittest
from unittest.mock import Mock, patch

import main
from minic.lexer import analisis_lexico
from minic.parser import analizar
from semantico.adaptador import programa_desde_arbol
from semantico.representacion import asig, decl, num, op, sentencia_if, sentencia_while, var


def representar(codigo):
    tokens, errores = analisis_lexico(codigo)
    if errores:
        raise AssertionError(errores)
    return programa_desde_arbol(analizar(tokens))


class PruebasAdaptador(unittest.TestCase):
    def test_conserva_precedencia_parentesis_y_asociatividad(self):
        programa = representar("int x; x = 10 - 4 - 1 + 2 * (3 + 5);")
        esperado = op("+", op("-", op("-", num(10), num(4)), num(1)),
                      op("*", num(2), op("+", num(3), num(5))))
        self.assertEqual(programa, [decl("int", "x"), asig("x", esperado)])
        self.assertEqual(representar("int x = 12 / 3 / 2;"), [
            decl("int", "x", op("/", op("/", num(12), num(3)), num(2)))
        ])

    def test_convierte_if_else_y_while_anidados(self):
        programa = representar(
            "int x = 0; while (x <= 3) { if (x != 1) { x = x + 1; } "
            "else { int y = 2; x = y; } }"
        )
        self.assertEqual(programa, [
            decl("int", "x", num(0)),
            sentencia_while(op("<=", var("x"), num(3)), [
                sentencia_if(op("!=", var("x"), num(1)),
                             [asig("x", op("+", var("x"), num(1)))],
                             [decl("int", "y", num(2)), asig("x", var("y"))]),
            ]),
        ])

    def test_programa_y_bloques_vacios(self):
        self.assertEqual(representar(""), [])
        self.assertEqual(representar("if (1 < 2) {}"), [
            sentencia_if(op("<", num(1), num(2)), [])
        ])


class PruebasIntegracionSemantica(unittest.TestCase):
    def setUp(self):
        # Prueba explícitamente el modo parcial, incluso cuando el equipo añada
        # el núcleo completo. Su selección se verifica en un caso independiente.
        seleccion = patch("main.importlib.util.find_spec", return_value=None)
        seleccion.start()
        self.addCleanup(seleccion.stop)

    def procesar(self, codigo):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            resultado = main.procesar_semantico(codigo)
        return resultado, salida.getvalue()

    def test_programa_valido_con_bloques_y_variables_exteriores(self):
        resultado, salida = self.procesar(
            "int x = 0; while (x < 3) { int y = x + 1; x = y; }"
        )
        self.assertTrue(resultado)
        self.assertIn("No se encontraron errores", salida)
        self.assertIn("Verificación parcial", salida)

    def test_rechaza_uso_y_asignacion_sin_declaracion(self):
        for codigo in ("x = 5;", "int x = y + 1;"):
            with self.subTest(codigo=codigo):
                resultado, salida = self.procesar(codigo)
                self.assertFalse(resultado)
                self.assertIn("no esta declarada", salida)

    def test_no_filtra_variables_entre_ambitos(self):
        casos = (
            "int x; if (1 < 2) { int y = 1; } x = y;",
            "int x; while (1 < 2) { int y = 1; } x = y;",
            "int x; if (1 < 2) { int y = 1; } else { x = y; }",
        )
        for codigo in casos:
            with self.subTest(codigo=codigo):
                resultado, salida = self.procesar(codigo)
                self.assertFalse(resultado)
                self.assertIn("'y'", salida)

    def test_errores_lexicos_o_sintacticos_no_llegan_al_verificador(self):
        for codigo, fase in (("int x = @;", "léxicos"), ("int x = ;", "sintácticos")):
            with self.subTest(fase=fase), patch("main.analizar_tipos") as verificador:
                resultado, salida = self.procesar(codigo)
                self.assertFalse(resultado)
                self.assertIn(fase, salida)
                verificador.assert_not_called()

    def test_informa_limite_de_redeclaraciones(self):
        resultado, salida = self.procesar("int x; int x;")
        self.assertTrue(resultado)  # El módulo de tipos no comprueba esta regla.
        self.assertIn("detección de redeclaraciones sigue pendiente", salida)
        self.assertNotIn("Entrada ACEPTADA", salida)

    def test_utiliza_el_nucleo_completo_cuando_existe(self):
        nucleo = types.ModuleType("semantico.analizador")
        nucleo.analizar_programa = Mock(return_value=(False, "Variable redeclarada: x."))
        with patch("main.importlib.util.find_spec", return_value=object()), patch.dict(
            sys.modules, {"semantico.analizador": nucleo}
        ), patch("main.analizar_tipos") as parcial:
            resultado, salida = self.procesar("int x; int x;")
        self.assertFalse(resultado)
        self.assertIn("Variable redeclarada", salida)
        self.assertNotIn("Verificación parcial", salida)
        nucleo.analizar_programa.assert_called_once_with([decl("int", "x"), decl("int", "x")])
        parcial.assert_not_called()

    def test_opcion_7_analiza_codigo_y_regresa_al_menu(self):
        salida = io.StringIO()
        entradas = ["7", "", "int x = 1;", "x = x + 1;", ":fin", "", "0"]
        with patch("builtins.input", side_effect=entradas), contextlib.redirect_stdout(salida), patch(
            "main._guardar_arbol"
        ) as visualizacion:
            main.menu()
        self.assertIn("7. Analizar semánticamente", salida.getvalue())
        self.assertIn("No se encontraron errores", salida.getvalue())
        self.assertIn("Hasta luego.", salida.getvalue())
        visualizacion.assert_not_called()


if __name__ == "__main__":
    unittest.main()
