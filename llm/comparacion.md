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
