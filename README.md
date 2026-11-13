# Proyecto TEO

**Gramáticas formales y lenguaje natural: experimentando los límites de la jerarquía de Chomsky**  
Asignatura: Teoría de Lenguajes de Programación.

## Integrantes

1. Julio Alberto Rodriguez Valencia — 00163922
2. Jose Everth Martinez Benavides — 00156021
3. Diego Alejandro Montoya Ramirez — 00087522
4. José Alfredo Rodríguez Rodríguez — 00055421

## Requisitos

- Python 3.10 o superior.
- Graphviz (recomendado) para exportar los árboles sintácticos a PNG o SVG. Si no está instalado, el programa guarda el grafo en formato DOT.
- spaCy y el modelo es_core_news_sm únicamente para ejecutar la demostración de comparacion/demo_spacy.py.
- Una clave de API y un modelo compatible con la Responses API y salidas JSON Schema estrictas para ejecutar el experimento LLM.

El lexer y los parsers propios utilizan la biblioteca estándar de Python. No se necesita instalar paquetes Python para probar mini-C, el parser propio del español o el menú.

## Instalación y ejecución

Clonar el repositorio y ubicarse en la carpeta raíz:

~~~bash
git clone https://github.com/julio22ar/Teo-Proyecto.git
cd Teo-Proyecto
~~~

Iniciar el menú integrador:

~~~bash
python main.py
~~~

En algunos sistemas el comando puede ser python3.

### Opciones del menú

1. **Analizar código mini-C.** Permite cargar un archivo o pegar código de varias líneas. Para finalizar la entrada pegada, escribir :fin en una línea independiente. Ejecuta análisis léxico y sintáctico e imprime el árbol.
2. **Analizar una oración en español reducido.** Ejecuta la gramática de espanol/gramatica_es.txt, muestra el árbol y el motivo de rechazo cuando no pertenece al subconjunto.
3. **Ejecutar pruebas mini-C.** Lanza los casos válidos e inválidos de pruebas/casos_minic.py.
4. **Demo exploratoria de spaCy.** Ejecuta comparacion/demo_spacy.py sobre los casos de pruebas/fallas.csv. Esta demostración exploratoria no sustituye la comparación cuantitativa de las 60 oraciones requerida en la Fase 2.
5. **Evaluar el parser propio con el corpus.** Procesa las 60 oraciones de pruebas/oraciones.csv y resume coincidencias y métricas frente a la columna esperado.
6. **Experimento LLM.** Permite preparar los archivos sin consultar la API o iniciar la ejecución real. La ejecución completa envía 120 solicitudes (60 oraciones en zero-shot y few-shot) y puede generar cargos según la cuenta del proveedor.

### Ejecutar mini-C desde un archivo

Se conserva el modo de ejecución directa:

~~~bash
python main.py minic/ejemplos/valido.txt
python main.py minic/ejemplos/invalido.txt
~~~

El programa muestra tokens, árbol sintáctico y el resultado de aceptación o rechazo.

## Visualización de árboles

arbol.py contiene la clase Nodo, imprimir_arbol() y dibujar_arbol(). Esta última exporta el árbol como PNG o SVG cuando encuentra el ejecutable dot de Graphviz. Las imágenes se guardan dentro de salidas/ (carpeta creada al ejecutar el menú). Sin Graphviz, se escribe el archivo fuente .dot para poder renderizarlo posteriormente.

Descarga e instalación de Graphviz: https://graphviz.org/download/. Después de instalarlo, verifique que dot esté disponible en el PATH y reinicie la terminal.

## Pruebas

Pruebas del parser mini-C:

~~~bash
python pruebas/casos_minic.py
~~~

Pruebas automatizadas del experimento LLM, que utilizan respuestas simuladas y no consultan servicios externos:

~~~bash
python -m unittest discover -s pruebas -p "test_llm.py" -v
~~~

## Experimento LLM

La configuración detallada se encuentra en llm/README.md. Para preparar los archivos sin clave ni llamadas a la API:

~~~bash
python -m llm.experimento --preparar
~~~

Para ejecutar el experimento:

1. Copiar .env.example a .env.
2. Definir OPENAI_API_KEY y OPENAI_MODEL en .env.
3. Revisar modelo, permisos y precios en la plataforma del proveedor.
4. Ejecutar python -m llm.experimento.

La clave se mantiene fuera del repositorio mediante .gitignore. No se deben publicar claves ni incorporarlas a capturas, logs o el informe.

## Estructura del repositorio

~~~text
Teo-Proyecto/
├── main.py                    menú integrador y punto de entrada
├── arbol.py                   nodos e impresión/visualización de árboles
├── minic/                     lexer, parser y gramática del mini-C
├── espanol/                   gramática, parser y vocabulario español reducido
├── pruebas/                   corpus, casos mini-C y pruebas automatizadas
├── comparacion/               demostración exploratoria con spaCy
├── llm/                       prompts, experimento API, logs y resultados
├── informe/                   borrador del informe y marco teórico
├── .env.example               plantilla de variables de entorno
└── README.md                  instrucciones del proyecto
~~~

## Estado de la Fase 2

El repositorio cuenta con el parser del español reducido y su gramática, un corpus de 60 oraciones y el módulo de experimento LLM. La demo spaCy actualmente trabaja con pruebas/fallas.csv; todavía debe completarse el pipeline de comparación de las 60 oraciones con las herramientas NLP elegidas, incluyendo medición de tiempos, métricas y gráficas. Los resultados reales del LLM requieren ejecutar las consultas con una clave configurada. El informe final debe completarse con las mediciones verificables del equipo, sin reemplazarlas por resultados simulados.

- Borrador actual del informe en Markdown: informe/informe.md.
- Marco teórico y bibliografía de trabajo: informe/marco_teorico.md.
- Instrucciones del experimento LLM: llm/README.md.
