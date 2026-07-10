# Prototipo de revisión ética temprana de ERS de IA

Estructura inicial del prototipo para analizar cobertura ética documental en Especificaciones de Requisitos de Software (ERS) de sistemas de IA.

El proyecto sigue la arquitectura definida durante el Sprint 5:

- entrada documental;
- normalización y preprocesamiento;
- segmentación y señales NLP;
- repositorio configurable de dimensiones, criterios y guardrails;
- motor de evaluación documental;
- agregación por rúbrica;
- recomendaciones;
- resultados revisables;
- persistencia y trazabilidad.

## Alcance de esta versión

Esta base corresponde a la primera tarea del Sprint 6: crear la estructura inicial del proyecto.

Incluye solamente la organización inicial del repositorio y las carpetas previstas para evolucionar el prototipo. Todavía no implementa carga real de documentos, normalización, almacenamiento, motor de evaluación ni endpoints.

## Estructura

```text
config/
├── .gitkeep
└── guardrails/
    └── .gitkeep
data/
├── input/
│   └── .gitkeep
└── output/
    └── .gitkeep
src/
└── etica_ia_ers/
    ├── configuration/
    ├── domain/
    ├── evaluation/
    ├── ingestion/
    ├── processing/
    ├── reporting/
    └── storage/
tests/
└── .gitkeep
```
