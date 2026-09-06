# Revisión ética temprana de ERS de IA

Prototipo académico para analizar la cobertura ética documental de una Especificación de Requisitos de Software (ERS) de un sistema de inteligencia artificial.

La aplicación carga una ERS, procesa su texto localmente, aplica un catálogo auditable de 72 guardrails y presenta cobertura, hallazgos, evidencias, alertas y recomendaciones para revisión humana.

## Demo funcional

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
python3 -m uvicorn etica_ia_ers.api:app --app-dir codigo_fuente --reload
```

Abrir [http://127.0.0.1:8000](http://127.0.0.1:8000). La pantalla permite:

- cargar archivos TXT, PDF con capa de texto y DOCX;
- indicar dominio e identificador documental opcionales;
- ejecutar el análisis completo desde el navegador;
- consultar cobertura e indicadores de D01 a D10;
- recorrer brechas, evidencia, hallazgos y recomendaciones;
- reabrir o eliminar documentos del historial local;
- preparar una ERS sintética de demostración sin buscar un archivo externo.

La documentación interactiva de la API queda disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Flujo implementado

```text
ERS TXT/PDF/DOCX
       │
       ▼
Carga y extracción de texto
       │
       ▼
Normalización, segmentación y clasificación
       │
       ▼
Actores, acciones, condiciones, vaguedad y ambigüedad
       │
       ▼
Motor ético + 72 guardrails D01-D10
       │
       ▼
Rúbrica y cobertura por dimensión
       │
       ▼
Alertas y recomendaciones documentales
       │
       ▼
API + interfaz web de revisión
```

| Dimensión | Tema |
| --- | --- |
| D01 | Propósito, contexto, alcance y límites |
| D02 | Actores, afectados e impactos previsibles |
| D03 | Datos, privacidad, calidad, acceso y retención |
| D04 | Equidad, grupos, proxies y mitigación de sesgos |
| D05 | Transparencia sobre el uso de IA |
| D06 | Explicabilidad de las salidas |
| D07 | Supervisión y control humano |
| D08 | Robustez, seguridad, fallas e incidentes |
| D09 | Responsabilidad, auditoría, reclamos y reparación |
| D10 | Impacto social, accesibilidad y sostenibilidad |

## Cómo leer el resultado

Cada guardrail produce un hallazgo preliminar `AUSENTE`, `PARCIAL` o `EXPLICITO`, con prioridad documental y evidencia trazable a fragmentos de la ERS. La cobertura de una dimensión conserva el nivel más débil de sus guardrails, una decisión prudente y reproducible definida por la rúbrica del proyecto.

El porcentaje de cobertura no ausente se calcula sobre dimensiones efectivamente evaluadas. Los errores de reglas y las dimensiones no cubiertas por el catálogo se muestran como advertencias, no como ausencias inventadas.

Las recomendaciones provienen de plantillas locales y versionadas. No se usa un LLM para generar el resultado y el documento no se envía a servicios externos.

## Alcance y límites

El prototipo evalúa **evidencia escrita en una ERS**. No prueba el comportamiento del software implementado, no audita modelos ni datasets reales y no determina cumplimiento legal. La salida no es una aprobación ni una certificación.

Esta versión no incluye:

- OCR para PDF escaneado;
- autenticación, usuarios o permisos;
- edición manual de la revisión humana;
- despliegue productivo;
- exportación del reporte, prevista en `SCRUM-112`.

Los documentos y su texto normalizado se guardan en `datos/almacenamiento/`. Evaluaciones y resultados se calculan con la versión activa del catálogo cada vez que se consultan; su persistencia completa queda fuera del prototipo actual.

## API

| Método | Ruta | Operación |
| --- | --- | --- |
| `GET` | `/salud` | Estado del servicio |
| `POST` | `/documentos` | Carga y normalización de una ERS |
| `GET` | `/documentos` | Historial local |
| `GET` | `/documentos/{id}/estado` | Estado del documento |
| `GET` | `/documentos/{id}/resultados` | Evaluación, cobertura y recomendaciones |
| `DELETE` | `/documentos/{id}` | Eliminación del registro local |

Ejemplo de carga:

```bash
curl -X POST "http://127.0.0.1:8000/documentos" \
  -F "archivo=@ejemplos/ers/scoring_crediticio.txt" \
  -F 'metadatos={"dominio":"crediticio"}'
```

## Estructura del código

```text
codigo_fuente/etica_ia_ers/
├── dominio/                         # contratos y tipos inmutables
├── entrada_documental/              # TXT, PDF y DOCX
├── procesamiento_textual_y_nlp/     # normalización y señales lingüísticas
├── modelo_etico_y_guardrails/       # catálogo D01-D10
├── evaluacion_documental/           # coordinación de reglas
├── rubrica_y_agregacion/            # cobertura e indicadores
├── recomendaciones/                 # alertas y plantillas de mejora
├── resultados_y_presentacion/       # serialización del reporte
├── persistencia_y_trazabilidad/     # almacenamiento local y bitácora
├── interfaz_web/                    # aplicación web sin build externo
└── api.py                            # endpoints e integración del flujo
```

Cada carpeta corresponde a una responsabilidad de la arquitectura. La interfaz usa HTML, CSS y JavaScript servidos por la misma aplicación FastAPI, por lo que no requiere Node.js ni un segundo servidor.

## Datos y ejemplos

`ejemplos/ers/` contiene tres ERS sintéticas, de elaboración propia, para scoring crediticio, diagnóstico médico y recomendación de contenidos. También puede ejecutarse el pipeline desde consola:

```bash
python3 ejemplos/analizar_ers.py
python3 ejemplos/analizar_ers.py ruta/a/otra_ers.txt
```

El almacenamiento local usa archivos JSON y TXT inspeccionables:

```text
datos/almacenamiento/
├── documentos/<uuid>/
│   ├── documento.json
│   ├── contenido.txt
│   ├── normalizacion.json
│   └── texto_normalizado.txt
└── trazabilidad.jsonl
```

El contenido de trabajo está ignorado por Git. Sólo se versiona `.gitkeep` para conservar el directorio base.

## Pruebas

```bash
python3 -m pytest
```

La suite genera documentos TXT, PDF y DOCX mínimos en memoria o en directorios temporales. Las únicas entradas versionadas son las ERS sintéticas de `ejemplos/ers/`; no se usan documentos académicos ni información externa.

GitHub Actions ejecuta la suite en cada pull request hacia `main`.

## Dependencias lingüísticas

El procesamiento usa spaCy 3.8.7 y `es_core_news_sm` 3.8.0. spaCy se distribuye bajo licencia MIT y el [modelo español](https://spacy.io/models/es) bajo GNU GPL 3.0. El modelo se instala desde su wheel oficial y no se almacena en el repositorio.

Los iconos de la interfaz derivan de [Lucide](https://lucide.dev), distribuido bajo licencia ISC.
