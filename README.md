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

Incluye contratos de dominio, configuración base, un ejemplo de guardrail versionado y pruebas mínimas de importación/configuración. Todavía no implementa carga real de documentos, normalización, almacenamiento ni endpoints.

## Estructura

```text
config/
├── analysis.default.json
└── guardrails/
    └── GR-D01-DELIM-USOS.v1.json
data/
├── input/
│   └── .gitkeep
└── output/
    └── .gitkeep
docs/
└── sprint-6-estructura-inicial.md
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
```

## Verificación local

Desde esta carpeta:

```bash
python3 -m unittest discover -s tests
```
