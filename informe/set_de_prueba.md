# Conjunto de prueba y niveles de complejidad

**Responsable** · Everth Martínez

El conjunto de prueba contiene 60 oraciones distintas, con 20 casos por nivel. Su propósito es medir la coincidencia de las decisiones de cada sistema con una referencia común y observar cuáles construcciones exceden la gramática reducida. Cada fila de `pruebas/oraciones.csv` identifica la oración con un número y registra el texto, el nivel, la decisión esperada y el fenómeno lingüístico. Las etiquetas se mantienen iguales para todos los sistemas. En los casos de nivel 3, la etiqueta puede ser `aceptar` aunque la gramática reducida deje fuera esa construcción.

| Nivel | Construcciones evaluadas | Aceptar | Rechazar |
| --- | --- | ---: | ---: |
| 1 · Simple | Sujeto, verbo y objeto en presente o pasado. Incluye errores de concordancia y orden, además de un objeto incompleto. | 14 | 6 |
| 2 · Intermedio | Adjetivos, adverbios, frases preposicionales y objeto con «a». Incluye modificadores con errores de concordancia o estructura. | 14 | 6 |
| 3 · Complejo | Subordinadas, coordinación, sujeto tácito, negación, clíticos, contracciones y posibles ambigüedades. Incluye errores de concordancia a distancia y en grupos coordinados. | 16 | 4 |
| **Total** | **60 casos** | **44** | **16** |

«El maestro leyó la carta» (ID 9) ilustra el patrón básico del primer nivel. «La niña pequeña mira las flores rojas» (ID 22) añade modificadores en sujeto y objeto. «El niño lee un libro que la maestra compró» (ID 43) introduce una relativa en el objeto y se etiqueta como aceptable. «El niño y la niña lee un libro» (ID 59) se etiqueta para rechazo porque el sujeto coordinado exige el verbo en plural.

Se verificaron los 60 identificadores, la ausencia de oraciones duplicadas y el balance por nivel. El vocabulario de los niveles 1 y 2 está cubierto por el léxico del parser. En el nivel 3 aparecen palabras fuera de ese inventario, como «que», «y», «no» y «del», asociadas a los fenómenos que se quieren poner a prueba. Por eso, un rechazo en ese nivel puede deberse al vocabulario, a las reglas sintácticas o a ambas cosas. Para interpretar los desacuerdos conviene consultar el fenómeno anotado y el mensaje del parser. El conjunto permite comparar los sistemas sobre estas 60 entradas y sus etiquetas.

**Fuente** · `pruebas/oraciones.csv`. Distribución visual reproducible con `python -m comparacion.graficas`.
