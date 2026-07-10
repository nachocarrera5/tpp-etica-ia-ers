# Sprint 6 - Estructura inicial del proyecto

## Objetivo

Crear una base de proyecto coherente con la arquitectura modular definida en Sprint 5, dejando preparados los puntos de extensión para las siguientes tareas del Sprint 6.

## Decisiones de estructura

| Carpeta | Propósito |
|---|---|
| `src/etica_ia_ers/ingestion` | Entrada documental, validación y registro de ERS |
| `src/etica_ia_ers/processing` | Extracción, normalización, segmentación y señales NLP |
| `src/etica_ia_ers/evaluation` | Selección y aplicación de guardrails |
| `src/etica_ia_ers/reporting` | Resultados, indicadores y recomendaciones |
| `src/etica_ia_ers/storage` | Persistencia y trazabilidad |
| `src/etica_ia_ers/configuration` | Carga de configuración y guardrails versionados |
| `src/etica_ia_ers/domain` | Contratos compartidos entre módulos |
| `config` | Configuración activa y ejemplos de guardrails |
| `data/input` | ERS de entrada locales, no versionadas |
| `data/output` | Resultados generados locales, no versionados |
| `tests` | Pruebas automatizadas mínimas |

## Trazabilidad con arquitectura

La estructura respeta los contratos conceptuales definidos en Sprint 5:

- Documento;
- Fragmento;
- Anotación NLP;
- Guardrail;
- Hallazgo;
- Resultado por dimensión;
- Recomendación;
- Configuración de análisis.

## Siguientes tareas del Sprint 6

1. Implementar carga de documentos ERS en `ingestion`.
2. Implementar normalización de texto en `processing`.
3. Implementar almacenamiento básico en `storage`.
4. Crear pantalla o endpoint inicial de carga y estado de análisis.

