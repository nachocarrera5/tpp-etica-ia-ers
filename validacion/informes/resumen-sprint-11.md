# Resumen de validacion del Sprint 11

## Cobertura

Se evaluaron 7 documentos, 10 dimensiones y 72 guardrails activos. Esto
produce 70 decisiones consolidadas de dimension y 504 aplicaciones de
guardrails. El corpus combina tres ERS sinteticas de control y cuatro
documentos reales de administracion publica y salud.

| Tarea | Dimensiones | Casos | Acuerdo de nivel | Precision | Exhaustividad | F1 |
|---|---|---:|---:|---:|---:|---:|
| SCRUM-120 | D01-D02 | 14 | 57,14% | 100,00% | 100,00% | 100,00% |
| SCRUM-121 | D03-D04 | 14 | 50,00% | 92,31% | 100,00% | 96,00% |
| SCRUM-122 | D05-D07 | 21 | 52,38% | 100,00% | 88,89% | 94,12% |
| SCRUM-123 | D08-D10 | 21 | 57,14% | 100,00% | 100,00% | 100,00% |
| **Total** | **D01-D10** | **70** | **54,29%** | **98,41%** | **96,88%** | **97,64%** |

## Lectura de resultados

El prototipo distingue bien entre dimensiones con y sin evidencia documental:
se observaron 62 verdaderos positivos, 5 verdaderos negativos, 1 falso
positivo y 2 falsos negativos. La precision y exhaustividad no deben
interpretarse como cumplimiento etico; sólo miden deteccion contra la
referencia preliminar.

El acuerdo exacto de nivel es sensiblemente menor. La causa dominante es una
subestimacion sistematica: los tres documentos sinteticos, redactados para
cubrir extensamente el catalogo, casi siempre quedan en `PARCIAL` en lugar de
`EXPLICITO`. Esto muestra que el motor encuentra evidencia, pero la combinacion
de señales lexicas y consolidacion es demasiado estricta para reconocer
cobertura completa expresada con formulaciones diversas.

## Casos para ajustar

1. **Falso positivo D04, SMS Murcia:** "por grupos" y "acciones correctivas"
   aparecen en soporte operativo, no en un analisis de equidad.
2. **Falso negativo D07, recomendador:** los controles del usuario, del adulto
   responsable y del comite no son reconocidos como supervision parcial.
3. **Falso negativo D06, Castilla-La Mancha:** una guia requerida de
   interpretabilidad constituye evidencia parcial, aunque no explicita.
4. **Graduacion de cobertura completa:** revisar señales y consolidacion para
   que una redaccion equivalente no genere una brecha artificial por cada
   frase no prevista literalmente.

## Limites

- La muestra es intencional y pequena; no representa todos los dominios ni
  estilos documentales.
- Los PDF reales son pliegos o fragmentos de especificaciones y no siempre una
  ERS pura bajo ISO/IEC/IEEE 29148.
- La referencia fue preparada mediante lectura asistida y debe recibir una
  segunda revision humana antes de publicarse como resultado definitivo.
- No se ajustaron reglas durante la medicion. La corrida queda como linea base
  para comparar los cambios de SCRUM-125.

## Conclusion

Las cuatro tareas validan que el flujo completo carga, procesa y evalua
documentos reales extensos sin errores, y que la deteccion de cobertura es
prometedora. No obstante, la validacion tambien demuestra que el nivel
`EXPLICITO` esta subdetectado y que existen tres errores semanticos concretos.
El modelo debe presentarse como apoyo preliminar a revision humana, no como una
clasificacion definitiva.
