## Comparación cuantitativa con herramientas de NLP

### Metodología

Se procesó el mismo conjunto de **60 oraciones** (etiquetadas en tres niveles
de complejidad y con su salida esperada *aceptar/rechazar*) con tres sistemas,
registrando para cada oración la decisión y el tiempo de ejecución:

- **Parser propio:** acepta una oración solo si pertenece a la gramática libre
  de contexto del español reducido (incluida la concordancia de género y número).
- **spaCy** (`es_core_news_sm`): es un analizador estadístico de dependencias
  que **siempre asigna un análisis** a cualquier entrada; carece de un juicio de
  gramaticalidad, por lo que su decisión se registra siempre como *aceptar*.
- **NLTK:** un etiquetador entrenado sobre el corpus `cess_esp` más una gramática
  libre de contexto general del español; acepta la oración si logra construir al
  menos un árbol de análisis.

La clase positiva es *aceptar*. Se calcularon, de forma global y por nivel:
**precisión** = TP/(TP+FP), **cobertura (recall)** = TP/(TP+FN) y **tasa de
rechazo correcto** = TN/(TN+FP), junto con la clasificación de errores en
**falsos positivos** (FP: acepta lo que debía rechazar) y **falsos negativos**
(FN: rechaza lo que debía aceptar).

### Resultados globales

| Sistema | Precisión | Recall | Rechazo correcto | FP | FN |
|---|---|---|---|---|---|
| Parser propio | 100,0 % | 68,2 % | 100,0 % | 0 | 14 |
| spaCy | 73,3 % | 100,0 % | 0,0 % | 16 | 0 |
| NLTK | 79,1 % | 77,3 % | 43,8 % | 9 | 10 |

El desglose por nivel se presenta en las figuras `metricas_por_nivel.png`
(precisión, recall y rechazo correcto) y `errores_por_nivel.png` (falsos
positivos y negativos).

### Análisis

Los tres sistemas ocupan posiciones claramente distintas:

- El **parser propio** no comete ningún falso positivo (0 FP) y alcanza una tasa
  de rechazo correcto del 100 %: **nunca acepta una oración agramatical**. Su
  limitación aparece como falsos negativos: rechaza 14 oraciones válidas, todas
  del nivel 3, porque contienen fenómenos (coordinación, subordinación a
  distancia, dependencias cruzadas) que exceden una CFG. Es, por tanto, un
  sistema **exacto pero estricto**, coherente con el carácter formal de una
  gramática libre de contexto.
- **spaCy** obtiene recall perfecto (100 %) precisamente porque acepta todo, pero
  su tasa de rechazo correcto es 0 % y acumula 16 falsos positivos: **no puede
  distinguir lo gramatical de lo agramatical**, ya que un modelo estadístico de
  dependencias siempre produce un análisis.
- **NLTK** se sitúa en un punto intermedio (43,8 % de rechazo correcto): su CFG
  general rechaza oraciones con orden incorrecto, pero acepta errores de
  concordancia de género y número que su gramática no modela.

### Costo computacional

El tiempo promedio por oración fue de **0,07 ms** para el parser propio,
**8,2 ms** para spaCy y **364,5 ms** para NLTK. El analizador formal es varios
órdenes de magnitud más rápido, mientras que el enfoque estadístico y el de
análisis sintáctico general son considerablemente más costosos.

### Conclusión de la sección

La evidencia cuantitativa confirma el límite teórico estudiado: un parser basado
en una CFG es preciso, rápido y capaz de rechazar lo agramatical, pero se queda
corto ante fenómenos sensibles al contexto; las herramientas modernas de NLP son
más flexibles y robustas al ruido, pero carecen de un criterio formal de
aceptación. Ningún enfoque domina en todas las métricas: cada uno responde a un
propósito distinto.
