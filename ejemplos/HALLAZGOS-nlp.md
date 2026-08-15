# Prueba del pipeline NLP con ERS de ejemplo (SCRUM-103)

Registro de la prueba integral del NLP al cierre del Sprint 7. El pipeline
ejercitado incluye carga, normalización, segmentación, clasificación, extracción
de actores, acciones y condiciones, y detección de ambigüedades y términos
vagos.

## Casos utilizados

Se versionan tres ERS de elaboración propia para los dominios previstos en la
validación:

- `scoring_crediticio.txt`;
- `diagnostico_medico.txt`;
- `sistema_recomendador.txt`.

Cada archivo se carga con el mismo cargador del prototipo y se procesa mediante
`analizar_texto`. El script `ejemplos/analizar_ers.py` permite reproducir el
reporte y `pruebas/prueba_nlp_ers_ejemplo.py` fija las expectativas verificables.

## Resultados

| ERS | Fragmentos | Anotaciones NLP |
|---|---:|---:|
| Diagnóstico médico | 14 | 26 |
| Scoring crediticio | 15 | 26 |
| Sistema recomendador | 14 | 27 |
| **Total** | **43** | **79** |

La prueba verifica:

- orden y tipo estructural de los fragmentos;
- clasificación funcional, no funcional, restricción, contexto y otro;
- presencia de actores, acciones, condiciones, ambigüedades y términos vagos;
- correspondencia exacta entre texto y offsets de cada anotación;
- justificación de las clasificaciones;
- reconocimiento de formas normativas como `podrá` y `queda prohibido`.

Las expresiones de calidad documental se incorporaron deliberadamente para
ejercitar las reglas: `completo`, `adecuada` y `cuando sea apropiado`. Son
señales para revisión humana y no conclusiones automáticas sobre la validez del
requisito.

## Límites

Esta prueba valida el comportamiento determinista del prototipo sobre ejemplos
controlados. No mide precisión, recall ni generalización sobre un corpus externo,
y tampoco evalúa todavía dimensiones éticas o suficiencia de evidencia. Esas
validaciones corresponden a tareas posteriores.
