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

Esta base corresponde al Sprint 6 del proyecto. Actualmente permite cargar documentos ERS y extraer su contenido textual en memoria.

La carga soporta archivos TXT con codificación UTF-8, PDF con capa de texto y DOCX. Todavía no implementa OCR, normalización, almacenamiento, segmentación, motor de evaluación ni endpoints.

## Instalación para desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

## Carga de una ERS

```python
from etica_ia_ers.ingestion import cargar_documento_desde_ruta

documento = cargar_documento_desde_ruta(
    "data/input/ers.txt",
    metadatos={"dominio": "crediticio"},
)

print(documento.nombre_original)
print(documento.contenido_extraido)
```

El cargador valida el formato y que exista texto procesable. La extracción no modifica el documento original ni escribe resultados en `data/`.

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
└── test_cargador_documentos.py
```
