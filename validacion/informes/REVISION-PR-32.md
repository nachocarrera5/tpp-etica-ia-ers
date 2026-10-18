# Revisión del PR 32 y ejecución del corpus

Revisión realizada el 18 de octubre de 2026. Los resultados usan la referencia
asistida existente, pendiente de segunda revisión humana. No constituyen una
validación independiente ni una certificación de cumplimiento.

## Correcciones

- La señal `validacion_profesional_obligatoria` exigía sólo «sin la validación
  de un profesional». Así clasificaba como explícita una decisión que permitía
  prescindir de supervisión. Ahora exige la prohibición de emitir, generar,
  comunicar o publicar el resultado sin esa revisión, dentro del mismo enunciado.
- La mención de RGPD, HIPAA o las leyes enumeradas se considera señal parcial
  del guardrail de consentimiento/base de tratamiento. Una cita normativa aislada
  no identifica el consentimiento ni la base concreta para tratar datos clínicos.
- Se incorporaron siete casos de regresión: cuatro negativos y tres variantes
  positivas de la prohibición de actuar sin supervisión.

## Corpus completo

Se volvió a ejecutar `validacion/ejecutar_validacion.py` sobre los siete PDF de
`corpus.csv`, usando `referencia_dimensiones.csv`. Se comparó main `65ffc16`,
el PR original `d2ea0d6`, el PR corregido `73256e0` y una integración local con
el PR 31 corregido `b3a3de3`.

| Variante | Hallazgos | Acuerdo de nivel | VP | VN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| main | 504 | 38/70 (54,29 %) | 62 | 5 | 1 | 2 |
| PR 32 original | 525 | 40/70 (57,14 %) | 63 | 5 | 1 | 1 |
| PR 32 corregido | 525 | 40/70 (57,14 %) | 63 | 5 | 1 | 1 |
| PR 31 + PR 32 corregidos | 525 | 40/70 (57,14 %) | 63 | 5 | 1 | 1 |

VP/VN/FP/FN comparan presencia de evidencia a nivel de dimensión, agrupando
PARCIAL y EXPLICITO. El acuerdo de nivel exige coincidencia en los tres niveles.
La precisión, exhaustividad y F1 de detección son 98,44 % en la integración,
siempre contra esta referencia preliminar y sobre 70 pares documento–dimensión.
No deben interpretarse como precisión de cada guardrail o de cada fragmento.

Cambios de dimensión frente a main:

- MEDICO-SINTETICO / D08: PARCIAL → EXPLICITO por la ponderación.
- RECOMENDADOR-SINTETICO / D07: AUSENTE → PARCIAL por las reglas del dominio,
  corrigiendo el caso VAL-002 de la referencia.

La corrección de la cita legal cambia SMS-MURCIA-REAL /
GR-D03-DELIM-SALUD-CONSENTIMIENTO de EXPLICITO a PARCIAL. El nivel de D03 no
cambia, lo que muestra por qué las métricas agregadas no sustituyen la revisión
de los hallazgos. El PR 31 no cambia los niveles del corpus común; sus ajustes
se verifican con las frases del pliego incluidas en sus pruebas.

Los 90 guardrails del catálogo no se aplican simultáneamente: cada documento
con dominio reconocido activa 72 generales y 3 específicos; los otros 15 no
son aplicables. Las siete ERS cubren salud, crédito, recomendación y sector
público. Empleo y educación mantienen únicamente pruebas sintéticas.

## Verificación adicional

- Integración de los dos PR: 658 pruebas aprobadas.
- Sintaxis JavaScript y `git diff --check`: sin errores.
- Navegador en modo público: análisis de la ERS de demostración con Salud,
  respuesta HTTP 200, 75 guardrails aplicados, 15 no aplicables y 0 errores;
  matriz por familias y columna del dominio; apertura del detalle del hallazgo.
  Sin errores en la consola del navegador durante ese recorrido.
- Reconsolidación de la línea base: se reproduce 39/70 al umbral del 85 %.
  Ese resultado aísla la ponderación y es distinto del 40/70 que incorpora
  también los guardrails de dominio.

Las reglas siguen siendo léxicas. Estas correcciones resuelven los casos
reproducidos y no equivalen a comprensión general de negaciones, contexto o
contradicciones. El umbral se ajustó sobre el mismo corpus; falta un conjunto
reservado y la segunda revisión de las etiquetas.

## Reproducción

```bash
PYTHONPATH=codigo_fuente python validacion/ejecutar_validacion.py \
  --corpus '/ruta/a/ERS de prueba' \
  --referencia validacion/referencia_dimensiones.csv \
  --salida /tmp/revision-pr32
PYTHONPATH=codigo_fuente python validacion/evaluar_ponderacion.py
python -m pytest -q
```
