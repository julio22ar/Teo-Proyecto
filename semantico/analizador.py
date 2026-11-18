from semantico.tabla_simbolos import TablaSimbolos, ErrorSemantico
from semantico.tipos import analizar_tipos


def _revisar_expresion(expr, tabla):
    """Revisa que todas las variables usadas en la expresion existan."""
    etiqueta = expr[0]
    if etiqueta == "var":
        nombre = expr[1]
        if tabla.buscar(nombre) is None:
            raise ErrorSemantico(
                "Variable no declarada: se usa '" + nombre +
                "' sin haberla declarado antes."
            )
    elif etiqueta == "op":
        _revisar_expresion(expr[2], tabla)   
        _revisar_expresion(expr[3], tabla)   
    


def _revisar_bloque_nuevo(sentencias, tabla, mostrar):
    """Abre un ambito, revisa las sentencias y lo cierra."""
    tabla.entrar_ambito()
    if mostrar:
        print("   { entra al ambito " + str(tabla.nivel()))
    _revisar_sentencias(sentencias, tabla, mostrar)
    if mostrar:
        print("   } sale del ambito " + str(tabla.nivel()) + " (se borran sus variables)")
    tabla.salir_ambito()


def _revisar_sentencias(sentencias, tabla, mostrar):
    for sentencia in sentencias:
        etiqueta = sentencia[0]

        if etiqueta == "decl":
            _, tipo, nombre, valor = sentencia
           
            if valor is not None:
                _revisar_expresion(valor, tabla)
            tabla.declarar(nombre, tipo)
            if mostrar:
                print("   declara '" + nombre + "' (" + tipo + ") en el ambito " + str(tabla.nivel()))
                tabla.mostrar()

        elif etiqueta == "asig":
            _, nombre, expr = sentencia
            if tabla.buscar(nombre) is None:
                raise ErrorSemantico(
                    "Variable no declarada: se asigna un valor a '" + nombre +
                    "' sin haberla declarado antes."
                )
            _revisar_expresion(expr, tabla)
            if mostrar:
                print("   usa '" + nombre + "': esta declarada, OK")

        elif etiqueta == "bloque":
            _revisar_bloque_nuevo(sentencia[1], tabla, mostrar)

        elif etiqueta == "if":
            _, cond, bloque_si, bloque_no = sentencia
            _revisar_expresion(cond, tabla)
            _revisar_bloque_nuevo(bloque_si, tabla, mostrar)
            if bloque_no is not None:
                _revisar_bloque_nuevo(bloque_no, tabla, mostrar)

        elif etiqueta == "while":
            _, cond, cuerpo = sentencia
            _revisar_expresion(cond, tabla)
            _revisar_bloque_nuevo(cuerpo, tabla, mostrar)

        else:
            raise ErrorSemantico("Sentencia desconocida: " + str(etiqueta))


def revisar_declaraciones(programa, mostrar=False):
    """Parte de Alex: declaracion previa, redeclaracion y ambitos.
    Devuelve (correcto, mensaje) sin lanzar excepcion."""
    tabla = TablaSimbolos()
    try:
        _revisar_sentencias(programa, tabla, mostrar)
        return True, "Declaraciones y ambitos correctos."
    except ErrorSemantico as error:
        return False, str(error)


def analizar_programa(programa, mostrar=False):
    """Analisis semantico completo. Devuelve (correcto, mensaje).
    Primero la tabla de simbolos (Alex) y despues los tipos (Diego)."""
    correcto, mensaje = revisar_declaraciones(programa, mostrar)
    if not correcto:
        return False, "ERROR SEMANTICO: " + mensaje

    correcto, mensaje = analizar_tipos(programa)
    if not correcto:
        return False, "ERROR SEMANTICO (tipos): " + mensaje

    return True, "Programa semanticamente correcto."


if __name__ == "__main__":
    from semantico.representacion import (
        PROGRAMA_VALIDO, PROGRAMA_VAR_NO_DECLARADA,
        PROGRAMA_REDECLARACION, PROGRAMA_TIPO_INCOMPATIBLE, mostrar,
    )

    casos = [
        ("PROGRAMA_VALIDO", PROGRAMA_VALIDO),
        ("PROGRAMA_VAR_NO_DECLARADA", PROGRAMA_VAR_NO_DECLARADA),
        ("PROGRAMA_REDECLARACION", PROGRAMA_REDECLARACION),
        ("PROGRAMA_TIPO_INCOMPATIBLE", PROGRAMA_TIPO_INCOMPATIBLE),
    ]
    for nombre, programa in casos:
        print("=" * 60)
        print(nombre)
        print("=" * 60)
        mostrar(programa)
        print("\nRecorrido de la tabla de simbolos:")
        correcto, mensaje = analizar_programa(programa, mostrar=True)
        print("\nResultado:", mensaje, "\n")
