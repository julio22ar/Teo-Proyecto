# Gramáticas formales y lenguaje natural

## Portada y autores

**Proyecto TEO — Teoría de Lenguajes de Programación.**
Integrante 5: Julio Alberto Rodriguez Valencia, 00163922.
Los demás autores se conservan en el [README](../README.md); completar los nombres
aún vacíos, docente, sección y fecha de entrega antes de presentar.

**Estado:** documento integrado a partir del código disponible. Los resultados
del LLM están pendientes de una ejecución real con credenciales. Las secciones
por tema permiten incorporar la revisión de cada integrante sin atribuir trabajos
a personas cuya distribución no se ha proporcionado.

## Resumen

El proyecto contrasta el reconocimiento formal de un mini-C y un subconjunto
del español con el comportamiento de un modelo de lenguaje. El código disponible
incluye un lexer y parser de mini-C, un reconocedor del español con concordancia,
un corpus de 60 oraciones y una demo de análisis con spaCy. El aporte del
Integrante 5 implementa un experimento por OpenAI API con prompts zero-shot y
few-shot, registro de respuestas y dos referencias de evaluación. La medición
separa aceptabilidad del español general de pertenencia al subconjunto formal.
Se entrega asimismo el marco teórico y una presentación reproducible.

## 1. Objetivos

- Relacionar tokens, estructuras sintácticas y dependencias entre símbolos con
  los distintos problemas que resuelve un compilador.
- Reconocer la diferencia entre una oración del español y una cadena generada
  por una gramática deliberadamente reducida.
- Medir si el LLM aplica las reglas solicitadas y cómo cambia su decisión al
  agregar ejemplos resueltos.
- Registrar evidencia suficiente para revisar cada respuesta y reproducir el
  procedimiento con el mismo corpus y configuración.

## 2. Fundamentos teóricos — aporte del Integrante 5

El desarrollo completo está en [marco_teorico.md](marco_teorico.md), con bibliografía.
Los tokens se describen mediante patrones regulares. Las CFG representan la
estructura jerárquica de expresiones y bloques; no resuelven automáticamente la
identidad de nombres arbitrarios, su declaración y visibilidad. Algunas
concordancias con rasgos finitos sí pueden desdoblarse en producciones de una CFG.

Por ello se distinguen tres preguntas: qué puede expresar una clase de gramáticas,
qué reglas incluye la gramática elegida y qué puede reconocer el parser concreto.
Un fallo en la tercera pregunta no demuestra una imposibilidad en la primera.
El [estudio de Shieber](https://www.eecs.harvard.edu/shieber/Biblio/Papers/shieber85.pdf)
analiza una familia de construcciones del alemán suizo; una oración aislada del
corpus español no reproduce esa prueba.

## 3. Análisis del lenguaje de programación — sección para revisión del responsable

### 3.1 Lexer

`minic/lexer.py` reconoce `int`, `if`, `else`, `while`, identificadores ASCII,
enteros, operadores aritméticos y comparadores, paréntesis, llaves y punto y coma.
Produce tokens con tipo, lexema y línea; reporta caracteres inválidos.
El lector debe distinguir este estado actual del requisito de columna, aún no
implementado en el código revisado.

### 3.2 Parser y árbol

`minic/parser.py` implementa descenso recursivo para las reglas de
`minic/gramatica.txt`. `arbol.py` permite construir e imprimir los árboles.
El punto de entrada `main.py` ejecuta lexer y parser. Los 25 casos existentes
de `pruebas/casos_minic.py` se aceptan o rechazan como establece esa suite.

### 3.3 Análisis semántico solicitado en Fase 1

En el código disponible no existe `semantico.py` ni una tabla de símbolos con
ámbitos, redeclaraciones y tipos. Esta sección queda identificada como pendiente
de la persona responsable; no se confunde la aceptación sintáctica con la
verificación de declaraciones. Su futura integración debe aportar implementación,
casos válidos e inválidos y evidencia de ejecución.

## 4. Español reducido y corpus — sección para revisión del responsable

`espanol/gramatica_es.txt` define sujeto explícito, verbo y objeto obligatorio,
con adjetivos, adverbios y frases preposicionales. `vocabulario.py` es un léxico
cerrado con rasgos de género, número y tiempo. `parser_es.py` devuelve aceptación,
árbol o mensaje de error y comprueba concordancia.

`pruebas/oraciones.csv` tiene 60 casos: 20 por nivel. Los dos primeros niveles
incluyen construcciones del subconjunto y errores de orden o concordancia. El
tercero explora relativas, coordinación, negación y otras construcciones más
amplias. Los niveles 1–3 del CSV son **niveles del corpus**, no los tipos 1–3
de la jerarquía de Chomsky.

El corpus etiqueta 44 casos como `aceptar` y 16 como `rechazar`. La referencia
del parser acepta 30 y rechaza 30. Se registran 14 casos etiquetados como
aceptables en español general que el subconjunto rechaza. Sus identificadores
son 41–53 y 56. Estas diferencias son casos de interés experimental, no
automáticamente defectos del parser.

## 5. Comparación con herramientas NLP — sección para revisión del responsable

`comparacion/demo_spacy.py` carga `es_core_news_sm`, obtiene categorías y
dependencias, y las muestra junto con la decisión del parser propio sobre
`pruebas/fallas.csv`. La anotación de dependencias y el reconocimiento de
pertenencia a una gramática son salidas distintas. Que spaCy produzca un análisis
no equivale a certificar que una oración sea gramatical o esté en el subconjunto.

No se incorporan cifras de spaCy ni HuggingFace: el modelo spaCy no se ejecutó en
esta revisión y no hay implementación de HuggingFace en los archivos revisados.
El responsable debe añadir su evidencia y explicar la procedencia de los casos.

## 6. Experimento LLM — aporte del Integrante 5

### 6.1 Pregunta y condiciones

¿Puede un LLM aplicar una gramática reducida aun cuando conozca construcciones
del español que esta no incluye? ¿Agregar cuatro ejemplos mejora esa adhesión?

Se usa OpenAI por API desde `llm/experimento.py`. Las dos condiciones reciben la
misma gramática y el mismo vocabulario; few-shot agrega cuatro ejemplos resueltos
que no coinciden con las oraciones evaluadas. Cubren aceptación, concordancia,
objeto obligatorio y coordinación no admitida. No se envían al modelo etiquetas,
resultados del parser ni niveles del corpus.

### 6.2 Procedimiento

1. Inspeccionar el corpus y ejecutar `python -m llm.experimento --preparar`.
2. Configurar `.env` con clave y modelo que admita Responses y JSON Schema.
3. Ejecutar un piloto en un directorio aparte y revisar formato, uso y acceso.
4. Ejecutar las 60 oraciones en ambos modos: 120 solicitudes independientes.
5. Conservar `configuracion.json`, `logs.txt`, `resultados_llm.csv` y `resumen.json`.
6. Revisar reglas y explicaciones de los desacuerdos, anotando `revision_manual`.
7. Incorporar al informe modelo solicitado y devuelto, fecha, cobertura y métricas.

Cada respuesta se guarda íntegramente, con solicitud, identificador y tokens.
La clave no se registra. Una huella identifica la configuración, que incluye
prompts, corpus efectivo y versión del parser. Al reanudar, se omiten respuestas
guardadas como correctas de formato (`ok`); ese estado no significa que el LLM
haya acertado la clasificación. No se repiten automáticamente solicitudes fallidas.

### 6.3 Métricas

Para cada modo, sobre `N` respuestas `ok`:

- **Exactitud respecto al corpus:** decisiones iguales a `esperado_corpus`, divididas por `N`.
- **Adhesión al subconjunto:** decisiones iguales a `esperado_cfg`, divididas por `N`.
- **Indicios de conocimiento general:** número de casos donde las referencias
  difieren y el LLM coincide con el corpus en lugar de la CFG.
- **Cobertura:** respuestas `ok` sobre las 60 esperadas por modo; errores aparte.

Los errores de API o formato no son clasificaciones. Con `N = 0`, los porcentajes
quedan sin definir (`null`), no en cero. Un indicio no demuestra el origen de la
decisión; se requiere revisar manualmente la justificación. Una regla inexistente
puede invalidar la explicación aunque la decisión binaria coincida.

### 6.4 Ejemplo de interpretación

«El niño lee.» tiene etiqueta `aceptar` en el corpus, pero el parser rechaza la
ausencia de objeto. Aceptarla aumenta la exactitud respecto al corpus y reduce
la adhesión al subconjunto. Por eso una cifra única de “aciertos” sería ambigua.
Rechazar «Un gato come una flor.» por resultar poco plausible sería otro tipo
de incumplimiento: las reglas no juzgan el sentido en el mundo real.

## 7. Resultados disponibles

| Componente | Evidencia local | Interpretación |
| --- | --- | --- |
| Mini-C | 25/25 casos existentes con el resultado esperado. | Validación sintáctica y el caso léxico incluido; no mide semántica. |
| Español, nivel 1 | 20/20 coincidencias con el corpus. | Incluye aceptación y rechazo. |
| Español, nivel 2 | 20/20 coincidencias con el corpus. | Incluye modificadores y concordancia. |
| Español, nivel 3 | 6/20 coincidencias; 14 desacuerdos. | Las 14 son oraciones aceptables fuera del subconjunto actual. |
| LLM zero-shot | Pendiente. | Completar tras recibir respuestas reales. |
| LLM few-shot | Pendiente. | Completar tras recibir respuestas reales. |

Tabla para completar a partir de `llm/resumen.json` después de la ejecución:

| Modo | Modelo devuelto y fecha | Completados/60 | Errores | Exactitud corpus | Adhesión CFG | Indicios |
| --- | --- | --- | --- | --- | --- | --- |
| zero-shot | Pendiente | — | — | — | — | — |
| few-shot | Pendiente | — | — | — | — | — |

No se afirma que few-shot sea mejor hasta contar con datos. Una corrida de 60
casos por condición es descriptiva; no demuestra superioridad general.

## 8. Discusión y limitaciones

La referencia formal es el parser del proyecto y puede contener defectos; los
desacuerdos deben cotejarse con las producciones escritas. El corpus es pequeño,
cerrado y no constituye una muestra representativa de todo el español.
Los cuatro ejemplos pueden favorecer específicamente las construcciones que
ilustran. La salida del modelo puede variar y el proveedor puede actualizar un
alias de modelo, por lo que se conservan respuestas y versiones devueltas.

Los conteos de tokens permiten describir consumo, pero el programa no calcula
precios ni garantiza un presupuesto. Los cargos dependen del modelo y las
condiciones de la cuenta; consultar la página del proveedor antes de ejecutar.
El cumplimiento de JSON Schema garantiza estructura de datos, no veracidad.

## 9. Conclusiones del estado actual

La implementación permite observar por separado tokenización, reconocimiento
sintáctico y aplicación de reglas del subconjunto del español. El aporte del
Integrante 5 deja preparado y probado el mecanismo de consulta y evaluación del
LLM. Los resultados empíricos de ese modelo todavía requieren credenciales y
ejecución real; la validación semántica de mini-C corresponde a una entrega
separada que aún no está en el código disponible.

Una CFG limitada y un LLM resuelven tareas diferentes si no se fija la consigna:
el primero decide pertenencia al lenguaje implementado; al segundo hay que pedirle
explícitamente esa misma pertenencia para poder medir adhesión a las reglas.
El experimento registra ambos criterios sin convertir errores del parser o
aceptabilidad cotidiana en conclusiones formales sobre todo el lenguaje natural.

## 10. Integración antes de entregar

- Completar portada y confirmar con el equipo la autoría de cada sección temática.
- Incorporar la sección semántica y sus evidencias cuando el responsable la entregue.
- Añadir resultados reales y revisión humana del experimento LLM.
- Añadir evidencia de la comparación NLP que efectivamente se haya ejecutado.
- Actualizar las diapositivas con los resultados finales, conservando su procedencia.

## Referencias y anexos

La bibliografía completa se encuentra en [marco_teorico.md](marco_teorico.md).
Instrucciones reproducibles: [llm/README.md](../llm/README.md).
Presentación: [diapositivas.md](diapositivas.md) y `diapositivas.pptx`.
Anexar la configuración, CSV y log de la corrida real seleccionada.
