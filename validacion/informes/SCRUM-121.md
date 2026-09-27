# SCRUM-121: Validar D03-D04

## Objetivo

Validar datos y privacidad (D03), y equidad y prevencion de sesgos (D04),
sobre el corpus comun del Sprint 11.

## Resultado

| Metrica | Valor |
|---|---:|
| Casos documento-dimension | 14 |
| Acuerdo exacto de nivel | 50,00% |
| Precision de deteccion | 92,31% |
| Exhaustividad de deteccion | 100,00% |
| F1 de deteccion | 96,00% |
| Falsos positivos | 1 |
| Falsos negativos | 0 |

## Diferencias observadas

- Las tres ERS sinteticas quedaron en `PARCIAL` para D03 y D04, pese a
  documentar datos, finalidad, calidad, acceso, retencion, atributos sensibles,
  grupos, metricas, responsables y mitigaciones.
- El pliego del Servicio Murciano de Salud produjo un falso positivo en D04.
  La expresion "por grupos" pertenece a un flujo de escalado de alertas y
  "acciones correctivas" describe soporte operativo; ninguna constituye por
  si sola evidencia de equidad o mitigacion de sesgos.

El caso confirma que una coincidencia debe considerar el contexto tematico y
no solamente terminos sueltos. Para SCRUM-125 se propone exigir una señal de
equidad, sesgo, discriminacion o comparacion de desempeno cercana a las
expresiones de grupos y acciones correctivas.

## Cierre

D03-D04 muestran buena recuperacion de evidencia, con un falso positivo
contextual localizado. La graduacion de los casos completos sigue siendo el
principal limite.
