# SCRUM-155: Incorporar ponderacion de guardrails

## Objetivo

Incorporar pesos a los guardrails para que la consolidacion por dimension
distinga una brecha menor de la falta de un criterio critico, sin ocultar
guardrails criticos ausentes (SCRUM-152) y sin convertir una cobertura
incompleta en `EXPLICITO` (SCRUM-124).

## Diseño

**Peso del guardrail.** Cada `DefinicionGuardrail` tiene un `peso_efectivo`.
Por defecto deriva de su prioridad documental, que ya expresa la criticidad
del criterio: `BAJA` = 1, `MEDIA` = 2 y `ALTA` = 3. El catalogo puede fijar un
`peso` explicito para un guardrail puntual. El motor copia el peso en cada
hallazgo, de modo que la rubrica no depende del catalogo para consolidar.

**Cobertura ponderada.** Por dimension se calcula

```text
cobertura ponderada = Σ (peso × aporte del nivel) / Σ peso
aporte: AUSENTE = 0, PARCIAL = 0,5, EXPLICITO = 1
```

El indicador global promedia la cobertura ponderada de las dimensiones
evaluadas. Es un indicador documental auxiliar: no es un puntaje etico.

**Guardrails criticos.** Son los hallazgos de prioridad `ALTA`. Los que no
llegan a `EXPLICITO` se informan en `guardrails_criticos_pendientes`.

**Regla de consolidacion.**

| Nivel | Condicion |
|---|---|
| `AUSENTE` | Ningun guardrail de la dimension tiene evidencia. |
| `EXPLICITO` | Todos los guardrails son explicitos, **o** la cobertura ponderada alcanza el 85% y no hay guardrails criticos pendientes. |
| `PARCIAL` | Cualquier otro caso. |

La ponderacion solo tolera brechas menores. Un guardrail critico parcial o
ausente mantiene la dimension en `PARCIAL`. Las brechas menores siguen en
`brechas_principales` y en la justificacion, aunque la dimension resulte
`EXPLICITO`.

## Calibracion del umbral

`evaluar_ponderacion.py` reconsolida los 504 resultados de guardrails de la
linea base de SCRUM-124 con la rubrica actual y la compara con
`referencia_dimensiones.csv`. No reprocesa los PDF, para aislar el efecto de
la ponderacion del de los cambios de señales.

| Regla | Acuerdo de nivel | `EXPLICITO` sobreestimado | `EXPLICITO` subestimado |
|---|---:|---:|---:|
| Linea base (todos explicitos) | 38/70 (54,29%) | 0 | 29 |
| Ponderada, umbral 70% | 37/70 (52,86%) | 2 | 28 |
| Ponderada, umbral 75% | 37/70 (52,86%) | 2 | 28 |
| Ponderada, umbral 80% | 38/70 (54,29%) | 1 | 28 |
| **Ponderada, umbral 85%** | **39/70 (55,71%)** | **0** | **28** |
| Ponderada, umbral 90% | 38/70 (54,29%) | 0 | 29 |
| Ponderada, umbral 95% | 38/70 (54,29%) | 0 | 29 |

Se adopta el 85%: es el unico umbral que mejora el acuerdo sin elevar
dimensiones que la referencia considera parciales. Con umbrales menores se
sobreestiman `ARAGON-REAL / D06` (82,35%) y `NOTAS-CLINICAS-REAL / D03`
(78,57%), ambos sin guardrails criticos pendientes.

El unico cambio con el umbral adoptado es `MEDICO-SINTETICO / D08`, que pasa
de `PARCIAL` a `EXPLICITO` (88,89%) con un unico guardrail no critico
ausente, en coincidencia con la referencia.

## Lectura

La ponderacion resuelve sólo una pequeña parte de la subestimacion registrada
en SCRUM-124. De los 28 casos que siguen en `PARCIAL` con referencia
`EXPLICITO`:

- 23 tienen al menos un guardrail critico sin evidencia explicita;
- 27 tienen una cobertura ponderada menor al 70% (mediana 43,75%).

La causa dominante es, entonces, la recuperacion lexica de las señales
explicitas y no la regla de consolidacion. Bajar el umbral para compensarla
generaria falsos `EXPLICITO`. El ajuste corresponde a SCRUM-125; la
ponderacion queda como criterio de graduacion estable para medir esos
cambios.

## Limites

- Los pesos derivan de la prioridad documental vigente; no fueron
  calibrados por separado.
- La referencia sigue pendiente de segunda revision humana.
- El corpus es pequeño e intencional; el umbral debe revisarse en SCRUM-127
  despues de los ajustes de SCRUM-125.

## Reproduccion

```bash
python validacion/evaluar_ponderacion.py
```

Los resultados se escriben en `validacion/resultados_ponderacion/`.
