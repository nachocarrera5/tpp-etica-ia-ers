# Prueba del pipeline NLP con ERS de ejemplo (SCRUM-103)

Registro de la prueba del NLP disponible al cierre del Sprint 7 sobre ERS de
ejemplo. El pipeline ejercitado es **normalización → segmentación → clasificación**
(SCRUM-96, SCRUM-99 y SCRUM-100). Todavía no incluye extracción de actores
(SCRUM-101) ni detección de ambigüedades (SCRUM-102).

## Qué se probó

- Tres ERS de ejemplo, redactadas como material propio para los dominios de alto
  riesgo previstos para la validación: `scoring_crediticio.txt`,
  `diagnostico_medico.txt` y `sistema_recomendador.txt` (carpeta `ejemplos/ers/`).
- Cada ERS se carga con el mismo cargador del prototipo y se procesa de extremo a
  extremo con `analizar_texto` (normaliza, segmenta y clasifica).
- La prueba automatizada `pruebas/prueba_nlp_ers_ejemplo.py` fija el
  comportamiento esperado; `ejemplos/analizar_ers.py` reproduce el reporte a mano.

Total: 43 fragmentos (15 + 14 + 14).

## Resultados

- **Segmentación:** los encabezados de sección (1, 2, 3, 4 y subniveles), los
  requisitos numerados, los ítems de lista y los párrafos se reconocen y se
  ordenan correctamente.
- **Clasificación:** todos los requisitos redactados con verbo normativo
  (`debe`/`deberá`) se clasifican como se espera:
  - requisitos funcionales → `REQUISITO_FUNCIONAL`;
  - requisitos de rendimiento, disponibilidad, seguridad y accesibilidad →
    `REQUISITO_NO_FUNCIONAL`;
  - prohibiciones (`no deberá…`) → `RESTRICCION`;
  - párrafos de propósito/alcance/contexto → `CONTEXTO`.
- **Señal de sección:** los fragmentos sin señal textual propia bajo
  "4. Restricciones" (un párrafo introductorio y un ítem de lista) se clasifican
  como `RESTRICCION` por su sección de origen, que es el comportamiento previsto.

## Limitación conocida

El segmentador decide encabezado-vs-requisito principalmente por la presencia de
un verbo normativo (`debe`, `deben`, `deberá`, `tendrá que`). Un requisito
redactado **sin** ese verbo y suficientemente corto se segmenta como
`ENCABEZADO`, por lo que no recibe categoría semántica y queda como `OTRO`.

Casos observados en las ERS de ejemplo:

| ERS | Ítem | Texto | Debería ser | Hoy |
|---|---|---|---|---|
| scoring_crediticio | 4.2 | "El sistema únicamente podrá operar con datos…" | RESTRICCION | ENCABEZADO/OTRO |
| sistema_recomendador | 4.2 | "Queda prohibido el uso de datos de ubicación…" | RESTRICCION | ENCABEZADO/OTRO |

Esto queda cubierto por la prueba `prueba_limitacion_conocida_requisito_sin_verbo_normativo`,
que falla de forma intencional si el segmentador se mejora, para recordar
actualizar el registro.

**Sugerencia para el backlog:** ampliar las formas normativas que reconoce el
segmentador (`podrá`, `queda prohibido`, `no podrá`, `se prohíbe`) al abordar
SCRUM-102 (detección de términos vagos) o un ajuste de SCRUM-99.
