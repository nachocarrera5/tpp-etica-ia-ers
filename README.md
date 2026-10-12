# Revisión ética temprana de ERS de IA

Prototipo académico para analizar la cobertura ética documental de una Especificación de Requisitos de Software (ERS) de un sistema de inteligencia artificial.

La aplicación carga una ERS, procesa su texto localmente, aplica un catálogo auditable de 72 guardrails generales y 18 específicos por dominio, y presenta cobertura, hallazgos, evidencias, alertas y recomendaciones para revisión humana.

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
- descargar el resultado en JSON, Markdown o HTML;
- reabrir o eliminar documentos del historial local;
- preparar una ERS sintética de demostración sin buscar un archivo externo.

La documentación interactiva de la API queda disponible en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Demo pública

El repositorio incluye un `Dockerfile` y un Blueprint `render.yaml` para desplegar la aplicación como un Web Service gratuito en Render.

La configuración de Render activa `MODO_PUBLICO=true`. En ese modo:

- la carga y el análisis se resuelven en una única solicitud a `POST /analisis`;
- la exportación usa `POST /reporte` sobre el resultado ya calculado;
- el documento se procesa en memoria y no se incorpora al historial;
- se deshabilitan los endpoints persistentes de listado, estado y eliminación;
- la interfaz informa el límite de 4 MB y oculta el panel de documentos;
- el contenido de la ERS no debe escribirse en logs.

Para comprobarlo localmente:

```bash
MODO_PUBLICO=true MAX_TAMANO_ARCHIVO_MB=4 \
  python3 -m uvicorn etica_ia_ers.api:app --app-dir codigo_fuente
```

La demo pública continúa siendo una herramienta académica preliminar. Aunque no retenga archivos, se recomienda no cargar información personal, confidencial ni sujeta a restricciones organizacionales.

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
Motor ético + 72 guardrails D01-D10 + 18 por dominio
       │
       ▼
Rúbrica y cobertura por dimensión
       │
       ▼
Alertas y recomendaciones documentales
       │
       ▼
API + interfaz web de revisión
       │
       ▼
Exportación JSON / Markdown / HTML
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

Cada guardrail produce un hallazgo preliminar `AUSENTE`, `PARCIAL` o `EXPLICITO`, con prioridad documental, peso y evidencia trazable a fragmentos de la ERS. Una dimensión es `AUSENTE` cuando ninguno de sus guardrails presenta evidencia, `PARCIAL` cuando combina evidencia con brechas o evidencia incompleta y `EXPLICITO` cuando todos sus hallazgos son explícitos o cuando sólo le quedan brechas menores. Esta consolidación mantiene una lectura exigente sin ocultar la evidencia encontrada.

### Guardrails específicos por dominio

Además del catálogo general, la ERS puede declarar el dominio del sistema en los metadatos (`{"dominio": "salud"}`) o desde el selector de la interfaz. Cada dominio suma tres guardrails propios, asociados a la dimensión que especializan:

| Dominio | Guardrails |
| --- | --- |
| Crédito y finanzas (`crediticio`) | Exclusión de variables protegidas (D04), motivos comunicados al solicitante (D06), impugnación de la decisión (D09) |
| Salud (`salud`) | Consentimiento y base legal de datos de salud (D03), decisión clínica final del profesional (D07), validación clínica del desempeño (D08) |
| Empleo (`empleo`) | Prevención de discriminación en la selección (D04), información a candidatos (D05), revisión humana de decisiones laborales (D07) |
| Educación (`educacion`) | Datos de estudiantes y menores (D03), equidad entre estudiantes (D04), revisión docente de decisiones académicas (D07) |
| Sector público (`sector_publico`) | Transparencia algorítmica (D05), vías de recurso (D09), canal alternativo no automatizado (D10) |
| Recomendación y contenidos (`recomendacion`) | Aviso de personalización (D05), control del usuario sobre la personalización (D07), protección de menores (D10) |

El dominio se reconoce también por alias habituales, como `Finanzas`, `Administración pública` o `Contenidos`. Los guardrails de otros dominios figuran como no aplicables. Si el dominio declarado no tiene guardrails específicos, el resultado lo advierte y se aplica sólo el catálogo general. Sus hallazgos participan de la consolidación y de la ponderación de su dimensión como cualquier otro guardrail.

### Ponderación de guardrails

Cada guardrail aporta a su dimensión según su peso. Por defecto el peso deriva de la prioridad documental (`BAJA` = 1, `MEDIA` = 2, `ALTA` = 3) y el catálogo puede fijar uno explícito. La cobertura ponderada de una dimensión es la suma de los pesos multiplicados por el aporte del nivel (`AUSENTE` = 0, `PARCIAL` = 0,5, `EXPLICITO` = 1), dividida por la suma de los pesos.

Una dimensión con hallazgos no explícitos se consolida como `EXPLICITO` sólo si su cobertura ponderada alcanza el 85 % **y** ningún guardrail de prioridad alta queda sin evidencia explícita. Los guardrails críticos pendientes se informan en cada dimensión y las brechas menores siguen visibles. El umbral se calibró contra la línea base de validación; el detalle está en `validacion/informes/SCRUM-155.md`.

El porcentaje de cobertura no ausente y la cobertura ponderada global se calculan sobre dimensiones efectivamente evaluadas. Los errores de reglas y las dimensiones no cubiertas por el catálogo se muestran como advertencias, no como ausencias inventadas.

Las recomendaciones provienen de plantillas locales y versionadas. No se usa un LLM para generar el resultado y el documento no se envía a servicios externos.

## Exportación del reporte

El reporte puede descargarse en tres formatos: `JSON` para intercambio con otras herramientas, `Markdown` para revisión y versionado junto al informe, y `HTML` como documento autocontenido, sin recursos externos y con estilos de impresión para guardarlo en PDF desde el navegador.

```bash
curl -OJ "http://127.0.0.1:8000/documentos/<id>/reporte?formato=html"
```

El parámetro `formato` acepta `json` (por defecto), `md` y `html`; un valor desconocido responde `400` con la lista de formatos válidos. La interfaz envía el resultado ya calculado a `POST /reporte`, disponible también en modo público. La exportación no reevalúa la ERS ni recalcula indicadores, y los tres formatos incluyen el aviso de alcance.

## Alcance y límites

El prototipo evalúa **evidencia escrita en una ERS**. No prueba el comportamiento del software implementado, no audita modelos ni datasets reales y no determina cumplimiento legal. La salida no es una aprobación ni una certificación.

Esta versión no incluye:

- OCR para PDF escaneado;
- autenticación, usuarios o permisos;
- edición manual de la revisión humana;
- despliegue productivo.

Los documentos y su texto normalizado se guardan en `datos/almacenamiento/`. Evaluaciones y resultados se calculan con la versión activa del catálogo cada vez que se consultan; su persistencia completa queda fuera del prototipo actual.

## API

| Método | Ruta | Operación |
| --- | --- | --- |
| `GET` | `/salud` | Estado del servicio |
| `GET` | `/configuracion-publica` | Modo y límites visibles de ejecución |
| `POST` | `/analisis` | Análisis completo en memoria, sin persistencia |
| `POST` | `/reporte` | Exportación de un resultado ya calculado, sin persistencia |
| `POST` | `/documentos` | Carga y normalización de una ERS |
| `GET` | `/documentos` | Historial local |
| `GET` | `/documentos/{id}/estado` | Estado del documento |
| `GET` | `/documentos/{id}/resultados` | Evaluación, cobertura y recomendaciones |
| `GET` | `/documentos/{id}/reporte` | Exportación del reporte en JSON, Markdown o HTML |
| `DELETE` | `/documentos/{id}` | Eliminación del registro local |

Los endpoints bajo `/documentos` se encuentran disponibles solamente en modo local. La demo pública utiliza `/analisis`.

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
├── resultados_y_presentacion/       # serialización y exportación del reporte
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

`ejemplos/exportar_reporte.py` ejecuta la cadena completa y escribe los reportes exportados en `datos/salida/`:

```bash
python3 ejemplos/exportar_reporte.py
python3 ejemplos/exportar_reporte.py ruta/a/otra_ers.txt --formato md
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

## Validacion del catalogo

`validacion/` contiene el protocolo, la referencia documental y los informes
de SCRUM-120 a SCRUM-123. La linea base evalua las diez dimensiones y los 72
guardrails sobre siete documentos, conservando separados el acuerdo exacto de
nivel y la deteccion de evidencia.

La corrida puede reproducirse con los PDF del corpus local:

```bash
python validacion/ejecutar_validacion.py \
  --corpus "/ruta/a/ERS de prueba" \
  --referencia validacion/referencia_dimensiones.csv \
  --salida /tmp/validacion-sprint-11
```

Los resultados son una validacion documental preliminar y requieren revision
humana. No representan cumplimiento, aprobacion ni certificacion del sistema.

## Dependencias lingüísticas

El procesamiento usa spaCy 3.8.7 y `es_core_news_sm` 3.8.0. spaCy se distribuye bajo licencia MIT y el [modelo español](https://spacy.io/models/es) bajo GNU GPL 3.0. El modelo se instala desde su wheel oficial y no se almacena en el repositorio.

Los iconos de la interfaz derivan de [Lucide](https://lucide.dev), distribuido bajo licencia ISC.
