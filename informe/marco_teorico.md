# Marco teórico: gramáticas formales, compilación y lenguaje natural

## 1. Lenguajes y jerarquía de Chomsky

Un alfabeto es un conjunto finito de símbolos; un lenguaje es un conjunto de
cadenas sobre ese alfabeto. Una gramática genera cadenas mediante producciones.
La jerarquía clasifica familias por restricciones en esas producciones y por los
modelos de cómputo capaces de reconocerlas. Las inclusiones son:

**regulares ⊊ libres de contexto ⊊ sensibles al contexto ⊊ recursivamente enumerables.**

| Tipo | Producciones y modelo asociado | Relación con el proyecto |
| --- | --- | --- |
| 3: regular | Gramáticas lineales a derecha o izquierda; autómatas finitos. | Patrones de tokens del lexer. |
| 2: libre de contexto | `A → α`, con un solo no terminal a la izquierda; autómatas de pila no deterministas. | Composición de expresiones y bloques; gramática reducida del español. |
| 1: sensible al contexto | Producciones no contractivas, con la excepción habitual para la cadena vacía; autómatas linealmente acotados. | Marco para estudiar dependencias más allá de las CFG; no es una clasificación automática de cada chequeo semántico. |
| 0: no restringida | Producciones generales; máquinas de Turing que reconocen el lenguaje. | Límite superior de la jerarquía, sin implementación en este proyecto. |

Las notas de [Cristopher Moore sobre autómatas, lenguajes y gramáticas](https://arxiv.org/abs/1907.12713)
desarrollan los modelos y relaciones de expresividad. La jerarquía describe
lenguajes potencialmente infinitos, no porcentajes de acierto en una muestra.

## 2. Lexer, parser y análisis semántico

El lexer agrupa caracteres en tokens: identificadores, números, operadores y
delimitadores. Una expresión regular describe la forma de un token y un autómata
finito basta para reconocer ese patrón. El parser trabaja sobre la secuencia de
tokens y construye una estructura jerárquica. Las lecciones 1, 3 y 4 de
[Sipser en MIT OpenCourseWare](https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/pages/lecture-notes/)
presentan expresiones regulares, CFG y su relación con autómatas de pila.

Ejemplo del proyecto:

```c
int x;
x = (2 + 3) * 4;
```

El lexer reconoce `int`, `x`, los números y signos. El parser identifica una
declaración y una asignación con una expresión anidada. Un analizador semántico
comprobaría además si `x` fue declarada, qué tipo tiene y en qué ámbito es visible.

Una regla sintáctica como `asignacion → ID = expresion ;` no enlaza por sí sola
cada identificador arbitrario con su declaración y ámbito. En compiladores se
usan tablas de símbolos y recorridos del árbol para mantener esa información.
La dependencia de nombres no acotados puede requerir comparar cadenas, algo que
no se obtiene simplemente añadiendo unas pocas producciones por categoría.
En cambio, algunas verificaciones con dominios finitos, como unas pocas clases
de tipos, pueden codificarse mediante desdoblamiento de no terminales. **No todo
chequeo llamado semántico demuestra por sí mismo que el lenguaje sea de Tipo 1.**

Estado observado: el repositorio tiene lexer y parser de mini-C, pero aún no
incluye `semantico.py`. El presente aporte no sustituye esa entrega ni afirma
que se hayan ejecutado comprobaciones de ámbitos o tipos.

## 3. Concordancia y gramática del español reducido

La concordancia finita de género y número puede expresarse en una CFG usando
categorías como `GN_ms`, `GN_fs`, `GN_mp` y `GN_fp`. El proyecto utiliza rasgos
en tuplas para implementar esas distinciones sin repetir funciones.
La concordancia sujeto-verbo se comprueba por el número del sujeto.

```text
El niño lee un libro.       → pertenece al subconjunto.
Los niños lee un libro.     → falla la concordancia.
El niño lee.                → falta el objeto que exige esta gramática.
```

La última oración muestra que aceptabilidad en español general y pertenencia
al lenguaje definido son preguntas diferentes. Además, una frase poco plausible
puede cumplir perfectamente la sintaxis: «Un gato come una flor.» no debe
rechazarse por conocimiento del mundo.

## 4. Límites de una gramática y límites de una implementación

Si el parser rechaza coordinación, relativas, negación o sujeto tácito, solo se
ha establecido que esas construcciones no están cubiertas por la implementación
actual. Se pueden agregar muchas de ellas mediante reglas libres de contexto.
La recursión por la izquierda dificulta un parser descendente ingenuo, pero no
es una limitación expresiva de todas las CFG: una implementación puede transformar
reglas o utilizar otra estrategia de análisis.

La ambigüedad significa que **una misma gramática** admite más de un árbol para
una cadena. Que una oración tenga dos lecturas en español no demuestra que la
gramática reducida genere ambos árboles; esta puede haber codificado solamente
una lectura. La frase «la maestra busca el libro en la mesa» es aceptada por el
parser del repositorio, que adjunta el complemento a un grupo nominal. Eso no
permite afirmar que el parser detectó o resolvió todas las lecturas posibles.

Para probar que un lenguaje no es libre de contexto hace falta un argumento
formal sobre una familia no acotada de cadenas. Un ejemplo clásico es el estudio
de dependencias cruzadas en alemán suizo de
[Shieber (1985)](https://www.eecs.harvard.edu/shieber/Biblio/Papers/shieber85.pdf).
El resultado se apoya en construcciones y supuestos lingüísticos específicos.
No autoriza a clasificar una oración española aislada con «respectivamente»
como demostración de no context-freeness. Tampoco basta que dos dependencias
se dibujen cruzadas: hay que especificar qué relaciones y cantidades se exigen.

## 5. Qué se mide al consultar a un LLM

Un LLM puede incorporar regularidades aprendidas del español que exceden el
subconjunto del proyecto. El experimento le pide aplicar exclusivamente las
reglas adjuntas, con dos condiciones: zero-shot, sin ejemplos resueltos, y
few-shot, con cuatro ejemplos externos al conjunto de evaluación.

Se comparan por separado la coincidencia con las etiquetas del corpus y la
coincidencia con el reconocedor formal. Una decisión que siga el español general
cuando este difiere del subconjunto constituye un indicio de apartarse de las
reglas; no revela el mecanismo interno que causó la respuesta. Por ello la
justificación y las reglas citadas requieren revisión humana.

La API ofrece un medio reproducible de enviar peticiones y registrar respuestas.
El esquema JSON facilita evaluar campos, pero **garantizar un formato no garantiza
una clasificación correcta**. La
[guía oficial de salidas estructuradas](https://developers.openai.com/api/docs/guides/structured-outputs)
describe el formato; las métricas y el diseño de evaluación son propios de este
proyecto.

## Referencias

1. Moore, C. (2019). *Lecture Notes on Automata, Languages, and Grammars*.
   https://arxiv.org/abs/1907.12713
2. Sipser, M. (2020). *18.404J Theory of Computation*, lecciones 1, 3 y 4.
   MIT OpenCourseWare. https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/pages/lecture-notes/
3. Shieber, S. M. (1985). *Evidence against the context-freeness of natural language*.
   Linguistics and Philosophy, 8, 333–343.
   https://www.eecs.harvard.edu/shieber/Biblio/Papers/shieber85.pdf
4. OpenAI. *Structured model outputs* y *Developer quickstart*.
   https://developers.openai.com/api/docs/guides/structured-outputs
   https://developers.openai.com/api/docs/quickstart

Fuentes consultadas el 13 de noviembre de 2026. Las afirmaciones sobre el estado
del software se basan en los archivos de este repositorio, no en las fuentes externas.
