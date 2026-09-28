# SCRUM-152: Evaluar cobertura etica, ambiguedad, verificabilidad y evidencia documental

## Objetivo

Evaluar cuatro propiedades observables del prototipo sobre el corpus comun del
Sprint 11:

1. cobertura etica consolidada por dimension;
2. señales de ambiguedad y terminos vagos;
3. presencia de evidencia para criterios de verificabilidad;
4. cantidad y consistencia de los vinculos de evidencia documental.

La medicion utiliza 7 documentos, 70 resultados de dimension y 504
aplicaciones de guardrails. Los resultados describen lo que detecta el
prototipo; no representan cumplimiento etico ni calidad del sistema real.
Los SHA-256 de los PDF se conservan en `resultados_calidad/hashes_corpus.csv`
para poder verificar que futuras corridas usen exactamente el mismo corpus.

## Resumen ejecutivo

| Eje | Resultado principal |
|---|---:|
| Dimensiones con alguna evidencia | 90,00% |
| Dimensiones con nivel EXPLICITO | 1,43% |
| Fragmentos con señal de ambiguedad o vaguedad | 3,31% |
| Señales de ambiguedad o vaguedad | 154 |
| Guardrails G-VERIF con evidencia | 45,24% |
| Aplicaciones de guardrail con evidencia | 46,43% |
| Vinculos de evidencia generados | 548 |
| Inconsistencias entre nivel y existencia de evidencia | 0 |

## 1. Cobertura etica documental

El motor consolido 7 dimensiones `AUSENTE`, 62 `PARCIAL` y 1 `EXPLICITO`.
Por lo tanto, el 90,00% presenta alguna evidencia, pero sólo el 1,43% alcanza
el nivel explicito.

| Documento | Ausentes | Parciales | Explicitas | No ausente | Explicita |
|---|---:|---:|---:|---:|---:|
| Diagnostico medico sintetico | 0 | 10 | 0 | 100% | 0% |
| Scoring sintetico | 0 | 10 | 0 | 100% | 0% |
| Recomendador sintetico | 1 | 9 | 0 | 90% | 0% |
| Aragon real | 0 | 9 | 1 | 100% | 10% |
| Castilla-La Mancha real | 2 | 8 | 0 | 80% | 0% |
| Notas clinicas real | 3 | 7 | 0 | 70% | 0% |
| SMS Murcia real | 1 | 9 | 0 | 90% | 0% |

La diferencia entre cobertura no ausente y cobertura explicita es demasiado
grande para interpretar el 90% como una cobertura etica satisfactoria. El
resultado significa que se encontro al menos una señal en la dimension, no que
todos sus criterios esten resueltos.

Las ERS sinteticas alcanzan 96,67% de cobertura no ausente, pero 0% explicita,
aunque fueron redactadas para cubrir el catalogo. Esto coincide con SCRUM-124:
el motor subestima `EXPLICITO` y la metrica refleja tanto el documento como la
calibracion de reglas y agregacion.

## 2. Ambiguedad y vaguedad

Se analizaron 4.024 fragmentos y 83.705 palabras normalizadas. El detector
marco 133 fragmentos y produjo 154 señales: 144 terminos vagos y 10
expresiones ambiguas.

| Tipo de documento | Señales | Señales cada 1.000 palabras |
|---|---:|---:|
| Sintetico | 4 | 0,86 |
| Real | 150 | 1,90 |

Los documentos reales presentan aproximadamente 2,2 veces mas señales por
1.000 palabras. Las reglas mas frecuentes corresponden a variantes de
"completo", "adecuado", "basico", "eficiente" y "suficiente". Entre las
expresiones ambiguas aparecen "en general", "segun corresponda", "siempre que
sea posible" y "en la medida de lo posible".

La normalizacion por palabras es mas comparable que la proporcion de
fragmentos: el pliego SMS se divide en 3.371 fragmentos, mientras que el caso
de notas clinicas sólo contiene 26. La segmentacion alteraria fuertemente una
comparacion basada unicamente en fragmentos.

Estas señales son alertas para revision. Un termino como "suficiente" puede
ser vago si no tiene criterio de aceptacion, pero puede ser valido si el mismo
fragmento define un umbral. El detector actual no interpreta ese contexto y su
vocabulario cerrado tampoco permite estimar falsos negativos sin una referencia
manual especifica de ambiguedad.

## 3. Verificabilidad

El catalogo contiene 18 guardrails `G-VERIF` por documento, 126 aplicaciones
en total. Sólo 57 encontraron evidencia `PARCIAL` o `EXPLICITO`, equivalente a
45,24%.

| Documento | G-VERIF con evidencia | Porcentaje |
|---|---:|---:|
| Diagnostico medico sintetico | 9 de 18 | 50,00% |
| Scoring sintetico | 10 de 18 | 55,56% |
| Recomendador sintetico | 7 de 18 | 38,89% |
| Aragon real | 12 de 18 | 66,67% |
| Castilla-La Mancha real | 7 de 18 | 38,89% |
| Notas clinicas real | 3 de 18 | 16,67% |
| SMS Murcia real | 9 de 18 | 50,00% |

Aragon presenta la mayor cobertura detectable de verificabilidad y el caso de
notas clinicas la menor. Sin embargo, el 48,15% obtenido por las ERS sinteticas
completas confirma que esta metrica tambien esta limitada por la recuperacion
lexica. No debe presentarse como una medida pura de calidad de los documentos.

## 4. Evidencia documental

De las 504 aplicaciones de guardrails, 234 tienen al menos un vinculo de
evidencia (46,43%). Se generaron 548 vinculos. La mediana entre aplicaciones
con evidencia es de uno en todos los documentos salvo Castilla-La Mancha, cuya
mediana es dos.

No se encontraron inconsistencias estructurales: cada hallazgo no ausente tiene
evidencia y cada hallazgo ausente carece de ella. Esto valida la integridad del
vinculo, pero no su relevancia semantica. SCRUM-124 ya registro un falso
positivo donde evidencia perfectamente trazada pertenecia a soporte operativo
y no a equidad.

La cantidad bruta tampoco es una medida de calidad. SMS Murcia genera 212
vinculos y uno de sus guardrails concentra 106 coincidencias por repeticion de
terminos en un pliego extenso. Para comparar documentos debe utilizarse la
proporcion de guardrails cubiertos y revisar la pertinencia de los fragmentos,
no premiar el volumen de coincidencias.

## Evaluacion conjunta

El prototipo demuestra tres fortalezas:

- procesa documentos reales extensos y produce resultados para D01-D10;
- mantiene trazabilidad estructural entre hallazgo y evidencia;
- permite localizar brechas, terminos revisables y criterios verificables.

Tambien quedan cuatro limites:

- cobertura no ausente no equivale a cobertura suficiente;
- `EXPLICITO` esta subdetectado;
- las alertas de ambiguedad son lexicas y dependientes del contexto;
- la cantidad de evidencias puede inflarse por longitud y repeticion.

En consecuencia, la salida es adecuada como apoyo a una revision humana
temprana, pero no como puntaje, certificacion ni decision automatica sobre la
calidad etica de una ERS.

## Trabajo derivado

1. SCRUM-125 debe ajustar las coincidencias y la calibracion registradas en
   SCRUM-124.
2. SCRUM-126 puede incorporar contexto a vaguedad y ambiguedad, y medirlo con
   una referencia manual especifica.
3. SCRUM-155 debe evaluar ponderacion sin ocultar guardrails criticos ausentes.
4. SCRUM-127 debe analizar las metricas posteriores al ajuste contra esta linea
   base.

Los CSV y el resumen JSON reproducibles se encuentran en
`validacion/resultados_calidad/`.
