# SCRUM-120: Validar D01-D02

## Objetivo

Validar la deteccion y graduacion de evidencia sobre proposito y contexto
(D01), y stakeholders e impacto (D02), utilizando tres ERS sinteticas de
control y cuatro documentos reales.

## Resultado

| Metrica | Valor |
|---|---:|
| Casos documento-dimension | 14 |
| Acuerdo exacto de nivel | 57,14% |
| Precision de deteccion | 100,00% |
| Exhaustividad de deteccion | 100,00% |
| F1 de deteccion | 100,00% |
| Falsos positivos | 0 |
| Falsos negativos | 0 |

El motor encontro evidencia de D01 y D02 en todos los documentos en los que
la referencia la esperaba. En los cuatro casos reales coincidió con el nivel
`PARCIAL`.

## Diferencias observadas

Las tres ERS sinteticas fueron clasificadas como `PARCIAL` en D01 y D02,
aunque la referencia las considera `EXPLICITO`. Los documentos incluyen
proposito, alcance, exclusiones, actores, afectados, supuestos, limitaciones e
impactos, pero algunas formulaciones no activan todos los guardrails lexicos.

No se recomienda ampliar palabras clave de forma aislada. El ajuste debe
revisar la cobertura conjunta de criterios y la regla de consolidacion para no
confundir una expresion diferente con una brecha real.

## Cierre

La deteccion de presencia para D01-D02 queda validada preliminarmente sobre el
corpus. La graduacion `PARCIAL/EXPLICITO` requiere ajuste y nueva medicion en
la tarea de refinamiento, conservando esta corrida como linea base.
