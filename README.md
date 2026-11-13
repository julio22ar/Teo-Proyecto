# Proyecto TEO 

Gramáticas formales y lenguaje natural: experimentando los límites de la jerarquía de Chomsky.

Teoría de Lenguajes de Programación

## Integrantes

1. 
2. Jose Everth Martinez Benavides 00156021
3. Diego Alejandro Montoya Ramirez 00087522
4. José Alfredo Rodríguez Rodríguez 00055421
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
├── llm/            prompts, experimento por OpenAI API y resultados
└── informe/        marco teórico, informe integrado y diapositivas
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

## LLM, teoría e informe

El experimento está implementado en [llm/experimento.py](llm/experimento.py).
Envía las 60 oraciones del corpus a OpenAI por API en los modos zero-shot y
few-shot; guarda las respuestas completas y evalúa por separado el acierto
respecto al corpus y la adhesión a la gramática reducida.

Preparar los archivos sin usar una clave ni consultar la API:

```powershell
python -m llm.experimento --preparar
```

Para ejecutar las 120 consultas, copiar `.env.example` como `.env`, configurar
`OPENAI_API_KEY` y `OPENAI_MODEL`, y ejecutar:

```powershell
python -m llm.experimento
```

La clave queda fuera del repositorio mediante `.gitignore`. Los archivos
preparados tienen estado `pendiente` hasta recibir respuestas reales.
Revisar [las instrucciones y criterios de evaluación](llm/README.md) antes de
ejecutar. No se necesitan paquetes de Python adicionales.

- [Marco teórico y bibliografía](informe/marco_teorico.md).
- [Informe integrado y estado de las secciones](informe/informe.md).