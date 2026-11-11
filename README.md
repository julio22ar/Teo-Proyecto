# Proyecto TEO 

Gramáticas formales y lenguaje natural: experimentando los límites de la jerarquía de Chomsky.

Teoría de Lenguajes de Programación

## Integrantes

1. 
2. 
3. 
4. 
5. Julio Alberto Rodriguez Valencia 00163922

## Requisitos

- Python 3 (probado con Python 3.10 o superior)
- El parser del mini-C no necesita instalar ninguna librería.

## Instalación

1. Descargar o clonar el repositorio.
2. Abrir una terminal dentro de la carpeta `proyecto-tlp`.

```
cd proyecto-tlp
```

## Ejecución

Todos los comandos se corren desde la carpeta raíz del proyecto.

Analizar un archivo con código del mini-C:

```
python main.py minic/ejemplos/valido.txt
python main.py minic/ejemplos/invalido.txt
```

Escribir el código directamente por teclado (una línea):

```
python main.py
```

El programa muestra los tokens, el árbol de análisis sintáctico y si la entrada fue ACEPTADA o RECHAZADA. Si hay un error indica la línea y qué se esperaba.

> En algunas computadoras el comando es `python3` en lugar de `python`.

## Estructura del proyecto

```
proyecto-tlp/
├── main.py         programa principal
├── arbol.py        clase Nodo e impresión del árbol (la usan todos los módulos)
├── minic/          lexer, parser y gramática del mini-C
├── espanol/        gramática y parser del español (pendiente)
├── pruebas/        casos de prueba y set de oraciones (pendiente)
├── comparacion/    comparación con spaCy y HuggingFace (pendiente)
└── llm/            prompts y logs del experimento con el LLM (pendiente)
```

## Lenguaje que reconoce el mini-C

Declaraciones `int`, asignaciones, `if / else`, `while` y expresiones aritméticas con `+ - * /` y paréntesis. La gramática completa está en `minic/gramatica.txt`.

Ejemplo de entrada válida:

```
int x = 5;
while (x < 10) {
    x = x + 1;
}
```
