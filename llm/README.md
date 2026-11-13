# Experimento LLM — Integrante 5

Clasifica las 60 oraciones de `pruebas/oraciones.csv` con OpenAI **por API desde
Python**, en dos modos: zero-shot (reglas) y few-shot (las mismas reglas más cuatro
ejemplos resueltos). No necesita paquetes adicionales; usa Python 3.10 o superior.

## Preparación sin API

Desde la raíz del repositorio:

```powershell
python -m llm.experimento --preparar
```

Genera `llm/configuracion.json`, `llm/resultados_llm.csv`, `llm/resumen.json` y
`llm/logs.txt`. Las 120 filas del CSV quedan **pendientes**, sin respuestas,
aciertos ni porcentajes inventados. El log está vacío hasta recibir respuestas.
La configuración contiene los textos completos de ambos prompts y la referencia
local; se puede inspeccionar antes de consultar al proveedor.

## Configurar OpenAI

1. Crear una cuenta de desarrollador y una clave desde la
   [plataforma de OpenAI](https://platform.openai.com/api-keys).
2. Consultar [precios](https://openai.com/api/pricing/) y disponibilidad de modelos
   en la cuenta. Este proyecto no presupone acceso gratuito ni fija un precio.
3. Copiar el archivo de ejemplo y editar la copia:

   ```powershell
   Copy-Item .env.example .env
   ```

   ```dotenv
   OPENAI_API_KEY=tu_clave_real
   OPENAI_MODEL=identificador_del_modelo
   ```

   El modelo debe admitir **Responses API y JSON Schema con `strict: true`**.
   Elegirlo según la [documentación de modelos](https://developers.openai.com/api/docs/models).
   No existe un modelo predeterminado para evitar seleccionar uno sin acceso en la cuenta.

La clave se carga desde `.env` o las variables de entorno. Las variables ya
definidas en el entorno tienen prioridad. `.gitignore` excluye `.env`; no pegar
la clave en el código, CSV, informe ni capturas. El programa no registra cabeceras
HTTP y oculta la clave si apareciera en una respuesta.

La integración sigue el [inicio rápido oficial](https://developers.openai.com/api/docs/quickstart)
y la guía de [salidas estructuradas](https://developers.openai.com/api/docs/guides/structured-outputs).

## Ejecutar el experimento

Primero se puede ejecutar un piloto de dos oraciones en un directorio aparte:

```powershell
python -m llm.experimento --limite 2 --salida llm/piloto
```

El experimento completo hace **120 solicitudes**: una por oración y modo.
Cada solicitud es independiente, sin historial de respuestas anteriores:

```powershell
python -m llm.experimento
```

También se puede indicar el modelo en la línea de comandos:

```powershell
python -m llm.experimento --modelo IDENTIFICADOR_DEL_MODELO
```

La clave nunca se pasa como argumento. `--modo zero-shot` o `--modo few-shot`
ejecuta un solo modo. `--max-tokens 2000` limita la salida por solicitud
(incluye tokens de razonamiento cuando corresponda); no es un límite monetario.
`--timeout 90` y `--pausa 0.5` controlan espera y separación entre solicitudes.
No se fija temperatura porque su compatibilidad depende del modelo; se conserva
el comportamiento predeterminado del proveedor. Para comparar modos, usar el
mismo modelo y configuración. Un identificador versionado mejora la trazabilidad.

## Archivos y reanudación

| Archivo | Contenido |
| --- | --- |
| `prompts.py` | Reglas comunes, léxico cerrado, ejemplos y esquema de respuesta. |
| `experimento.py` | Cliente HTTP, evaluación, persistencia y CLI. |
| `configuracion.json` | Modelo solicitado, corpus efectivo, prompts, parámetros y huellas. |
| `logs.txt` | Una línea JSON por intento: petición, respuesta íntegra, fecha, estado y error. |
| `resultados_llm.csv` | Una fila por oración y modo; 120 filas en la corrida completa. |
| `resumen.json` | Totales, cobertura, exactitud y adhesión por modo. |

Repetir **el mismo comando** reanuda la corrida: omite respuestas `ok` y reintenta
los casos con error o pendientes. El log es la fuente para reconstruir el CSV.
Los comentarios de `revision_manual` del CSV se conservan al actualizarlo.
El programa se detiene ante el primer error; no reintenta automáticamente
solicitudes que podrían generar nuevos cargos. Después de un timeout, revisar el
uso del proveedor antes de repetir: la solicitud pudo haberse procesado.

Cambiar modelo, corpus efectivo, modos, prompts, parser o límite de tokens exige
otro `--salida` cuando ya existen intentos registrados. Así no se mezclan
experimentos. Se permite regenerar una preparación sin respuestas para configurar
el modelo. Un log truncado se reporta para reparación explícita, sin descartar
silenciosamente respuestas que pudieran volver a cobrarse.

## Cómo interpretar los resultados

El campo `esperado` del corpus indica aceptabilidad del español general. **No es
siempre la decisión que corresponde a la gramática reducida.** Por eso se usan
dos referencias separadas:

- `acerto_corpus`: decisión del LLM igual a `esperado` del corpus.
- `respeto_reglas`: decisión del LLM igual a la del parser de español reducido.
  Es una medida de adhesión en la **decisión**, no prueba que la explicación sea correcta.
- `indicio_conocimiento_general`: `si` cuando ambas referencias difieren y el
  LLM coincide con el corpus en lugar de la CFG. Es un indicio observable de
  apartarse de la consigna, **no prueba del proceso interno del modelo**. `no`
  significa que ese indicio no se observó; no demuestra ausencia de conocimiento previo.
- `revision_manual`: comentario humano sobre la regla y explicación, por ejemplo
  «justifica con una producción inexistente» o «decisión correcta, motivo incorrecto».

Ejemplo: «El niño lee.» es aceptable en español, pero la gramática del proyecto
exige un objeto. Si el LLM la acepta, acierta el corpus y no respeta esta regla.
Si la rechaza por la ausencia de objeto, cumple la consigna formal aunque no
coincida con la etiqueta del corpus.

Los errores HTTP, rechazos del servicio, respuestas incompletas y JSON inválido
se marcan como `error`, con métricas vacías; **no cuentan como rechazos gramaticales**.
Los porcentajes usan únicamente respuestas `ok`; informar también completados
sobre total. El modelo se registra tanto en su identificador solicitado como en
el devuelto por la API, junto con tokens y `response_id`.

El parser es una referencia operativa del repositorio, no un oráculo infalible.
Revisar manualmente desacuerdos relevantes contra `gramatica_es.txt`. El corpus
finito no permite demostrar la clase formal de todo el español ni que un LLM
implemente un autómata de una clase particular.

## Pruebas sin red

```powershell
python -m unittest discover -s pruebas -p test_llm.py -v
```

Las respuestas simuladas se usan exclusivamente en directorios temporales de
prueba; nunca se presentan como mediciones del modelo real.
