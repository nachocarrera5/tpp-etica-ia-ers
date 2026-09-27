# SCRUM-123: Validar D08-D10

## Objetivo

Validar robustez y seguridad (D08), accountability y auditoria (D09), e
impacto social y ambiental (D10).

## Resultado

| Metrica | Valor |
|---|---:|
| Casos documento-dimension | 21 |
| Acuerdo exacto de nivel | 57,14% |
| Precision de deteccion | 100,00% |
| Exhaustividad de deteccion | 100,00% |
| F1 de deteccion | 100,00% |
| Falsos positivos | 0 |
| Falsos negativos | 0 |

## Diferencias observadas

El motor detecto correctamente presencia o ausencia en los 21 casos. Las
nueve diferencias de nivel corresponden a los tres documentos sinteticos,
clasificados como `PARCIAL` aunque especifican umbrales, fallas, contingencia,
monitoreo, responsables, registros, versionado, reclamos, accesibilidad,
autonomia y sostenibilidad.

La clasificacion `EXPLICITO` de D10 para el caso Aragon fue revisada sobre las
evidencias: el pliego identifica afectados, exige accesibilidad con pruebas de
usuarios, permite revertir salidas, fija objetivos ambientales y contempla
mitigacion. Por ello se mantiene como coincidencia valida y no como falso
positivo.

## Cierre

D08-D10 alcanzan deteccion perfecta en este corpus preliminar. El trabajo
pendiente es calibrar el nivel de los casos documentados de forma completa,
sin relajar la deteccion en los documentos reales parciales.
