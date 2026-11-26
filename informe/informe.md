# Gramáticas formales y lenguaje natural

## Portada y autores

**Proyecto TEO — Teoría de Lenguajes de Programación.**
Integrante 5: Julio Alberto Rodriguez Valencia, 00163922.
Los demás autores se conservan en el [README](../README.md); completar los nombres
aún vacíos, docente, sección y fecha de entrega antes de presentar.

**Estado:** documento integrado a partir del código disponible.
<!-- LLM_ESTADO_INICIO -->
El experimento LLM está completado: 120 respuestas reales registradas; los resultados se presentan en la sección 7.
<!-- LLM_ESTADO_FIN -->
Las secciones
por tema permiten incorporar la revisión de cada integrante sin atribuir trabajos
a personas cuya distribución no se ha proporcionado.

## Resumen

En mini-C estudiamos cómo se reconoce una expresión y cómo se comprueba que las
variables que contiene están declaradas y son visibles. Para el español, comparamos
un parser de gramática reducida con spaCy y NLTK sobre 60 oraciones etiquetadas.
Con esas mismas oraciones evaluamos si un modelo de lenguaje, consultado por API,
aplica las reglas del subconjunto. Las etiquetas del corpus y las decisiones del
parser ofrecen dos referencias para interpretar sus respuestas.

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

## 3. Análisis de mini-C

### 3.1 Lexer

`minic/lexer.py` reconoce `int`, `if`, `else`, `while`, identificadores ASCII,
enteros, operadores aritméticos y comparadores, paréntesis, llaves y punto y coma.
Cada token conserva el tipo, el lexema y la línea y columna donde comienza,
contadas desde 1. El lexer también localiza caracteres inválidos como `@` y
literales mal formados como `12abc`.

### 3.2 Parser y árbol

`minic/parser.py` implementa descenso recursivo para las reglas de
`minic/gramatica.txt`. `arbol.py` permite construir e imprimir los árboles.
Por ejemplo, en `x = 2 + 3 * 4;` el árbol agrupa la multiplicación dentro de la
suma. La asignación tiene la estructura exigida incluso si todavía falta
declarar la variable `x`.

### 3.3 Declaraciones, ámbitos y tipos

La opción 7 de `main.py` ejecuta el lexer y el parser. Si ambos aceptan la
entrada, el adaptador convierte el árbol en sentencias que recorre el analizador
semántico. La tabla de símbolos mantiene un diccionario por ámbito y busca cada
nombre desde el bloque actual hacia el exterior. Rechaza una segunda declaración
en el mismo bloque y permite que una declaración interior oculte temporalmente
a otra exterior. El verificador de tipos comprueba inicializaciones, asignaciones
y expresiones. Los operadores aritméticos trabajan con enteros y las condiciones
de `if` y `while` requieren una comparación de tipo booleano.

```c
int x;
if (1 == 1) {
    int y = 2;
    x = y;
}
x = y;
```

Dentro del bloque están visibles tanto `x` como `y`. Al cerrarse la llave termina
el ámbito de `y`. La última asignación tiene la misma forma que la anterior y el
analizador semántico la rechaza porque ya no encuentra la declaración de `y`.

## 4. Español reducido y corpus

`espanol/gramatica_es.txt` define sujeto explícito, verbo y objeto obligatorio,
con adjetivos, adverbios y frases preposicionales. `vocabulario.py` es un léxico
cerrado con rasgos de género, número y tiempo. `parser_es.py` devuelve aceptación,
árbol o mensaje de error y comprueba concordancia.

Los tres niveles del corpus agrupan 60 oraciones distintas según las
construcciones que ponen a prueba. Cada fila identifica la oración, el nivel,
el fenómeno lingüístico y la decisión esperada en español. Todos los sistemas
se evalúan con las mismas etiquetas. [Corpus de evaluación](../pruebas/oraciones.csv)

| Nivel | Construcciones y ejemplos del corpus | Aceptar | Rechazar |
| --- | --- | ---: | ---: |
| 1 · Simple | Sujeto, verbo y objeto en presente o pasado. «El maestro leyó la carta.» (ID 9). Se prueban también el orden y la concordancia. | 14 | 6 |
| 2 · Intermedio | Adjetivos, adverbios, frases preposicionales y objeto con «a». «La niña pequeña mira las flores rojas.» (ID 22). | 14 | 6 |
| 3 · Complejo | Relativas, coordinación, sujeto tácito, negación, clíticos y contracciones. «El niño lee un libro que la maestra compró.» (ID 43). | 16 | 4 |
| **Total** | **20 oraciones por nivel** | **44** | **16** |

La etiqueta del caso 43 es *aceptar*. El parser reducido lo rechaza porque su
léxico y sus producciones dejan fuera la relativa introducida por «que». En el
mismo nivel, «El niño y la niña lee un libro.» (ID 59) lleva la etiqueta
*rechazar* por la discordancia entre el sujeto coordinado y el verbo singular.
El nivel señala la complejidad del ejemplo y admite ambos resultados.

## 5. Comparación del parser propio con spaCy y NLTK

Se registraron tres decisiones y tres tiempos por oración. El **parser propio**
acepta cuando reconoce la cadena completa con la gramática reducida. **spaCy**
produce un análisis de dependencias con `es_core_news_sm`. El programa de
comparación registra *aceptar* cuando obtiene ese análisis. En **NLTK**, un
etiquetador entrenado con `cess_esp` asigna categorías a las palabras y un
`ChartParser` acepta si una segunda CFG construye al menos un árbol sobre esas
categorías. Esta gramática incluye reglas para coordinación y subordinación.
[Procedimiento de comparación](../comparacion/comparar.py) · [Gramática de NLTK](../comparacion/herramienta_nltk.py)

Tomamos *aceptar* como clase positiva. La **precisión** indica qué proporción de
las aceptaciones del sistema concuerda con el corpus. La **cobertura** indica qué
proporción de los 44 casos aceptables recupera. El **rechazo correcto** mide
cuántos de los 16 casos etiquetados para rechazo descarta. Un falso positivo (FP)
es una aceptación incorrecta y un falso negativo (FN) es un rechazo incorrecto.

| Sistema | Precisión | Cobertura | Rechazo correcto | FP | FN | Tiempo medio por oración |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parser propio | 100,0 % | 68,2 % | 100,0 % | 0 | 14 | 0,07 ms |
| spaCy | 73,3 % | 100,0 % | 0,0 % | 16 | 0 | 8,2 ms |
| NLTK | 79,1 % | 77,3 % | 43,8 % | 9 | 10 | 364,5 ms |

El parser propio coincidió con las 40 etiquetas de los niveles 1 y 2. Sus 14
falsos negativos se concentraron en el nivel 3 (IDs 41–53 y 56). Algunos de esos
casos admiten una extensión de la propia CFG. Por ejemplo, una producción para
sujetos coordinados podría cubrir «El niño y la niña» junto con una regla de
concordancia plural. Los rechazos delimitan la cobertura de las reglas y del
vocabulario que implementó el equipo.

En spaCy, las 60 entradas recibieron análisis. La convención de registrarlas como
aceptadas explica tanto la cobertura del 100 % como los 16 falsos positivos.
NLTK recuperó 34 de las 44 oraciones aceptables, pero también aceptó «El niña lee
un libro.» (ID 15). Su gramática agrupa determinantes y sustantivos en categorías
que omiten el género. [Decisiones por oración](../comparacion/resultados.csv) · [Métricas por nivel](../comparacion/metricas.csv)

Los tiempos corresponden a la corrida registrada. En NLTK, la primera oración
incluyó el entrenamiento del etiquetador y tardó 21,7 segundos. Esa observación
eleva la media a 364,5 ms por oración. La mediana de las 60 mediciones fue 1,93 ms.

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
7. Ejecutar `python -m llm.comparar --actualizar-informe` para cotejar los registros
   y completar las tablas con modelo solicitado y devuelto, fechas y métricas.

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
| Mini-C, lexer y parser | 25/25 casos en `python -m pruebas.casos_minic`. | Se aceptaron las 12 entradas válidas y se rechazaron las 13 inválidas. |
| Mini-C, pruebas léxicas y semánticas | 32/32 casos en `python -m pruebas.casos_lexico_semantico`. | Pasaron 8 casos del lexer, 11 del verificador de tipos y 13 del analizador semántico integrado. Estos últimos incluyen redeclaración, sombreado y uso fuera de ámbito. |
| Español, nivel 1 | 20/20 coincidencias con el corpus. | Incluye aceptación y rechazo. |
| Español, nivel 2 | 20/20 coincidencias con el corpus. | Incluye modificadores y concordancia. |
| Español, nivel 3 | 6/20 coincidencias; 14 desacuerdos. | Las 14 son oraciones aceptables fuera del subconjunto actual. |

<!-- LLM_RESULTADOS_INICIO -->
### Comparación zero-shot y few-shot

Modelo solicitado: `gpt-5.4-mini-2026-03-17`. Corrida completa: **120/120 respuestas ok**.
Las fechas siguientes corresponden a America/El_Salvador (UTC-6).

| Modo | Modelo devuelto y fecha | Completados/60 | Errores finales | Exactitud corpus | Adhesión CFG | Indicios |
| --- | --- | --- | --- | --- | --- | --- |
| zero-shot | gpt-5.4-mini-2026-03-17; 17/11/2026 14:34 a 17/11/2026 14:37 | 60/60 | 0 | 45/60 (75.00%) | 53/60 (88.33%) | 3 |
| few-shot | gpt-5.4-mini-2026-03-17; 17/11/2026 14:37 a 17/11/2026 14:39 | 60/60 | 0 | 47/60 (78.33%) | 59/60 (98.33%) | 1 |

El cambio de few-shot respecto a zero-shot es **+10.00 puntos porcentuales en adhesión** y **+3.33 en exactitud del corpus**.
La adhesión es la métrica que responde directamente a la consigna de aplicar la gramática reducida. Una exactitud mayor en el corpus puede provenir de aceptar construcciones del español general fuera del subconjunto.

| Nivel del corpus | Modo | Aciertos corpus | Respeta CFG | Indicios |
| --- | --- | --- | --- | --- |
| 1 | zero-shot | 18/20 | 18/20 | 0 |
| 1 | few-shot | 20/20 | 20/20 | 0 |
| 2 | zero-shot | 18/20 | 18/20 | 0 |
| 2 | few-shot | 20/20 | 20/20 | 0 |
| 3 | zero-shot | 9/20 | 17/20 | 3 |
| 3 | few-shot | 7/20 | 19/20 | 1 |

| Comparación sobre las mismas 60 oraciones | Cantidad |
| --- | --- |
| Ambos modos respetan la CFG | 53 |
| Solo few-shot respeta la CFG | 6 |
| Solo zero-shot respeta la CFG | 0 |
| Ninguno respeta la CFG | 1 |

| Modo | Tokens de entrada | Tokens de salida | Explicaciones con revisión anotada |
| --- | --- | --- | --- |
| zero-shot | 135860 | 8314 | 0/60 |
| few-shot | 155180 | 5528 | 0/60 |

Los tokens de esta tabla corresponden a las respuestas finales ok; no incluyen intentos previos fallidos ni constituyen una factura. Un indicio no demuestra el proceso interno del modelo. La coincidencia de decisión tampoco valida la explicación: su revisión se anota en `revision_manual` del CSV.

#### Oraciones cuya decisión cambia

| ID | Oración | Referencia CFG | Zero-shot | Few-shot |
| --- | --- | --- | --- | --- |
| 3 | Los perros buscan la pelota. | aceptar | rechazar | aceptar |
| 14 | Unos gatos comieron las flores. | aceptar | rechazar | aceptar |
| 23 | Los perros pequeños buscan la pelota roja. | aceptar | rechazar | aceptar |
| 30 | Los niños de la casa roja compran unos libros. | aceptar | rechazar | aceptar |
| 48 | El niño lee. | rechazar | aceptar | rechazar |
| 49 | Lee un libro. | rechazar | aceptar | rechazar |

Son resultados descriptivos de una corrida de este corpus; no demuestran superioridad general de un modo ni la clase formal de todo el español.
<!-- LLM_RESULTADOS_FIN -->

### Lectura de los resultados y casos seleccionados

En esta corrida, few-shot corrigió seis decisiones de zero-shot y no introdujo
nuevos desacuerdos con la CFG. Los dos modos respetaron las reglas en 53 casos;
few-shot lo hizo además en los casos 3, 14, 23, 30, 48 y 49. El único desacuerdo
compartido con el reconocedor reducido fue el caso 53.

| Casos | Observación registrada | Interpretación respecto a las reglas |
| --- | --- | --- |
| 3 y 23 | Zero-shot rechazó oraciones con «buscan» y puso en duda que el verbo estuviera en el vocabulario. Few-shot las aceptó. | `buscan` sí está definido como presente plural. Las decisiones de zero-shot son rechazos incorrectos. |
| 14 | Zero-shot devolvió `rechazar`, pero su propia explicación describe «Unos gatos comieron las flores.» como una estructura válida. Few-shot devolvió `aceptar`. | Hay contradicción entre decisión y explicación en zero-shot. La métrica conserva el campo `decision` original, sin reinterpretarlo ni corregir la respuesta. |
| 30 | Zero-shot rechazó «Los niños de la casa roja compran unos libros.» por situar «roja» fuera de la estructura. Few-shot la aceptó. | La frase preposicional contiene su propio grupo nominal, «la casa roja», cuyo adjetivo sí está permitido; zero-shot interpretó incorrectamente el anidamiento. |
| 48 y 49 | Zero-shot aceptó «El niño lee.» y «Lee un libro.»; few-shot las rechazó. | La CFG exige objeto y sujeto explícito, respectivamente. Few-shot se ajustó al subconjunto aunque esas dos decisiones no coincidan con las etiquetas del español general. |
| 53 | Ambos modos aceptaron «El niño lee el libro rápidamente en el parque.». | La CFG permite el adverbio final del predicado, pero no una frase preposicional adicional después de ese adverbio. El parser deja «en» sin consumir y rechaza la entrada. Ambos modos ampliaron la estructura admitida. |

La separación entre métricas es especialmente visible en el nivel 3: few-shot
mejoró la adhesión de 17/20 a 19/20, mientras su exactitud respecto al corpus bajó
de 9/20 a 7/20. Esto se explica por los casos 48 y 49: rechazarlos es correcto
para la consigna formal y contrario a sus etiquetas de aceptabilidad general.

Los indicios de apartarse de las reglas hacia la etiqueta general bajaron de
tres a uno. Este patrón no demuestra que el modelo haya recurrido internamente
a conocimiento general; el caso 53 también puede explicarse por una lectura
incorrecta de las producciones. Las explicaciones de zero-shot en los casos 3,
14 y 23 muestran además que un JSON válido no garantiza coherencia del contenido.

Esta es una revisión asistida de casos seleccionados, no una certificación humana
de las 120 explicaciones. Las columnas `decision_llm`, `regla_llm` y
`explicacion_llm` y las respuestas originales se conservaron sin correcciones.
El campo `revision_manual` queda disponible para las observaciones del equipo.
El piloto, guardado por separado en `llm/piloto/`, no forma parte de estas 120
mediciones ni de las métricas de la tabla.

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

## 9. Conclusiones

En mini-C, una misma asignación puede ser válida dentro de un bloque y fallar
fuera de él. Los patrones regulares del lexer reconocen los mismos tokens en
ambas apariciones y el parser construye la misma estructura. La tabla de símbolos
permite explicar la diferencia al identificar qué declaración sigue visible. Así
se observa en un programa concreto qué aporta cada etapa del análisis.

En español, el parser reducido reconoció 30 de las 44 oraciones que el corpus
etiqueta como aceptables y rechazó las 16 etiquetadas como incorrectas. Los 14
desacuerdos muestran qué construcciones habría que añadir para ampliar el
subconjunto. Determinar los límites de todas las gramáticas libres de contexto
requiere un argumento sobre familias de cadenas. En esta comparación también
influyó cómo se definió *aceptar*: obtener dependencias en spaCy permitió contar
un análisis para cada entrada, mientras que construir un árbol en NLTK dependió
de las categorías y producciones elegidas.

En las 120 respuestas del LLM, añadir cuatro ejemplos elevó la coincidencia con
la gramática de 53/60 a 59/60. La diferencia se aprecia en «El niño lee.» y
«Lee un libro.»: *few-shot* rechazó ambas por las reglas de objeto obligatorio
y sujeto explícito. Ese cambio mejoró la adhesión al subconjunto aunque las dos
oraciones son aceptables según el corpus. La elección de la referencia determina
qué pregunta responde cada porcentaje.

## 10. Integración antes de entregar

- Completar portada y confirmar con el equipo la autoría de cada sección temática.
- Revisar las tablas reales ya incorporadas y añadir la revisión humana de las
  explicaciones del experimento LLM.
- Actualizar las diapositivas con los resultados finales, conservando su procedencia.

## Referencias y anexos

La bibliografía completa se encuentra en [marco_teorico.md](marco_teorico.md).
Instrucciones reproducibles: [llm/README.md](../llm/README.md).
Presentación: Subir presentación powerpoint y la referencia de la ruta
