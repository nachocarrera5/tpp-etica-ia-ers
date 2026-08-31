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

El prototipo permite cargar documentos ERS, extraer y normalizar su contenido textual, segmentarlo, clasificar sus fragmentos e identificar actores, acciones, condiciones, términos vagos y expresiones ambiguas. También almacena los documentos y su normalización junto con el estado del análisis y una bitácora de trazabilidad, e incorpora la infraestructura extensible del motor de evaluación ética.

La carga soporta archivos TXT con codificación UTF-8, PDF con capa de texto y DOCX. El endpoint inicial ejecuta carga, normalización y almacenamiento antes de informar el estado. Todavía no implementa OCR, guardrails reales D01-D10, agregación por dimensión ni exposición del motor mediante endpoints.

## Instalación para desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

La instalación incluye spaCy 3.8.7 y el modelo español `es_core_news_sm` 3.8.0. El procesamiento se realiza localmente: los fragmentos no se envían a servicios externos. spaCy se distribuye bajo licencia MIT y el [modelo español](https://spacy.io/models/es) bajo GNU GPL 3.0; el modelo se instala desde su wheel oficial y no se almacena en este repositorio.

## Carga de una ERS

```python
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta

documento = cargar_documento_desde_ruta(
    "datos/entrada/ers.txt",
    metadatos={"dominio": "crediticio"},
)

print(documento.nombre_original)
print(documento.contenido_extraido)
```

El cargador valida el formato y que exista texto procesable. La extracción no modifica el documento original ni escribe resultados en `datos/`.

## Segmentación y clasificación

La clasificación distingue requisitos funcionales, requisitos no funcionales, restricciones, contexto y otros fragmentos. Cada resultado conserva el fragmento original e informa las señales y la justificación de la regla aplicada.

```python
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.procesamiento_textual_y_nlp import (
    NormalizadorDeTexto,
    clasificar_fragmentos,
    segmentar,
)

documento = cargar_documento_desde_ruta("datos/entrada/ers.txt")
normalizado = NormalizadorDeTexto().normalizar(documento.contenido_extraido)
fragmentos = segmentar(normalizado.normalizado)
resultados = clasificar_fragmentos(fragmentos)

for resultado in resultados:
    print(resultado.clasificacion.value, resultado.justificacion)
```

Las reglas normalizan mayúsculas y acentos sólo para buscar señales; no modifican el texto ni los offsets del fragmento. La clasificación tampoco asigna niveles éticos `Ausente`, `Parcial` o `Explícito`: esa decisión corresponde a cada guardrail aplicable del motor de evaluación.

`analizar_texto` ejecuta el pipeline NLP completo sobre un texto de ERS ya extraído. Devuelve el texto normalizado, los fragmentos clasificados y las anotaciones de actores, acciones, condiciones, ambigüedades y términos vagos:

```python
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto

resultado = analizar_texto(documento.contenido_extraido)

for fragmento in resultado.fragmentos_clasificados:
    print(fragmento.fragmento.texto, fragmento.clasificacion.value)

for anotacion in resultado.anotaciones:
    print(anotacion.tipo_senal.value, anotacion.valor_detectado)
```

## Extracción de actores, acciones y condiciones

El extractor combina el análisis morfológico y de dependencias de spaCy con reglas explícitas para condiciones y roles habituales en una ERS. Cada señal conserva el UUID del fragmento, su texto exacto, offsets, metadatos lingüísticos y las versiones del procesador y del modelo.

```python
from etica_ia_ers.procesamiento_textual_y_nlp import extraer_de_fragmentos

anotaciones = extraer_de_fragmentos(fragmentos)

for anotacion in anotaciones:
    print(
        anotacion.tipo_senal.value,
        anotacion.valor_detectado,
        anotacion.metadatos,
    )
```

Los actores incluyen sujetos responsables, agentes pasivos, destinatarios y personas u organizaciones afectadas. Las acciones contienen el verbo principal y sus complementos; las condiciones conservan expresiones como `cuando`, `si`, `ante` o `dentro de`.

## Detección de ambigüedades y términos vagos

El detector aplica patrones léxicos auditables sobre cada fragmento. Las coincidencias respetan palabras completas y variantes habituales de género, número y acentuación, evitando falsos positivos como detectar `util` dentro de `utilizar`. El resultado usa el mismo contrato `AnotacionNLP`, con UUID, offsets relativos al fragmento y la regla aplicada.

```python
from etica_ia_ers.procesamiento_textual_y_nlp import detectar_en_fragmentos

senales_calidad = detectar_en_fragmentos(fragmentos)

for senal in senales_calidad:
    print(senal.tipo_senal.value, senal.valor_detectado, senal.metadatos["regla"])
```

Estas coincidencias son señales para revisión y no prueban por sí solas que el requisito sea incorrecto. La suficiencia de evidencia, el contexto del dominio y los niveles éticos corresponden al motor de evaluación.

## Motor de evaluación ética

`MotorEvaluacionEtica` consume un `ResultadoAnalisisNLP`, selecciona las versiones activas del repositorio y registra cada ejecución como `APLICADO`, `NO_APLICABLE` o `ERROR`. Cada guardrail decide su aplicabilidad, nivel, prioridad y evidencias; el motor coordina esas reglas, verifica la trazabilidad de los fragmentos y aísla los errores para continuar con las reglas restantes.

```python
from etica_ia_ers.dominio import SolicitudEvaluacionEtica
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_D01_D02,
    GUARDRAILS_D03_D04,
    GUARDRAILS_D05_D07,
    GUARDRAILS_D08_D10,
    RepositorioGuardrailsEnMemoria,
)

guardrails = (
    GUARDRAILS_D01_D02
    + GUARDRAILS_D03_D04
    + GUARDRAILS_D05_D07
    + GUARDRAILS_D08_D10
)
repositorio_guardrails = RepositorioGuardrailsEnMemoria(guardrails)
motor = MotorEvaluacionEtica(repositorio_guardrails)
resultado_etico = motor.evaluar(
    SolicitudEvaluacionEtica(
        documento_id=documento.id,
        resultado_nlp=resultado,
        metadatos={"dominio": "crediticio"},
    )
)
```

## Cobertura ética documental e indicadores

La capa `rubrica_y_agregacion` consolida los hallazgos del motor por dimensión y calcula indicadores globales, por grupo temático, familia de guardrail y prioridad documental:

```python
from etica_ia_ers.rubrica_y_agregacion import calcular_cobertura_etica

cobertura = calcular_cobertura_etica(resultado_etico)

print(cobertura.resultados_por_dimension)
print(cobertura.indicadores_globales)
print(cobertura.indicadores_por_grupo)
```

Cuando una dimensión contiene hallazgos mixtos, se conserva el nivel más débil para producir una lectura prudente y explicable. La prioridad máxima y la necesidad de revisión humana se calculan de manera independiente del nivel.

Los porcentajes se calculan únicamente sobre dimensiones efectivamente evaluadas. Si el catálogo todavía no produjo hallazgos para alguna dimensión, ésta se informa en `dimensiones_no_evaluadas` y no se interpreta como `AUSENTE`. El resultado también advierte sobre guardrails con error o evaluaciones sin dimensiones cubiertas.

Estos indicadores resumen cobertura documental; no constituyen un puntaje ético, una aprobación ni una certificación. El cálculo opera en memoria y no incluye persistencia, endpoints, visualización, exportación o recomendaciones.

El catálogo actual incorpora guardrails léxicos y auditables para D01-D10: propósito y contexto, stakeholders e impacto, datos y privacidad, equidad y sesgos, transparencia, explicabilidad, supervisión humana, robustez y seguridad, accountability y auditoría, e impacto social y ambiental. Cada regla conserva las señales y fragmentos que justifican el nivel, mientras que la prioridad responde a la criticidad configurada para el guardrail y no se deriva automáticamente de `AUSENTE`, `PARCIAL` o `EXPLICITO`.

La salida representa cobertura ética documental preliminar: no acredita cumplimiento, no certifica el sistema y no evalúa su comportamiento real. En esta etapa tampoco hay carga JSON/YAML, persistencia de evaluaciones ni recomendaciones finales.

## Ejemplos de ERS y prueba del pipeline NLP

`ejemplos/ers/` contiene tres ERS de ejemplo, de elaboración propia, para los dominios de scoring crediticio, diagnóstico médico y sistema recomendador. El script `ejemplos/analizar_ers.py` ejecuta el pipeline completo e imprime clasificaciones y señales NLP sin escribir en disco:

```bash
python3 ejemplos/analizar_ers.py
python3 ejemplos/analizar_ers.py ruta/a/otra_ers.txt
```

`ejemplos/HALLAZGOS-nlp.md` resume el alcance y los resultados observados. La validación automatizada equivalente está en `pruebas/prueba_nlp_ers_ejemplo.py`.

## Endpoints

Para levantar la API desde la raíz del proyecto:

```bash
python3 -m uvicorn etica_ia_ers.api:app --app-dir codigo_fuente
```

### Carga
```bash
curl -X POST "http://127.0.0.1:8000/documentos" \
  -F "archivo=@datos/entrada/ers.txt" \
  -F 'metadatos={"dominio":"crediticio"}'
```

### Estado de análisis
```bash
curl "http://127.0.0.1:8000/documentos/<documento_id>/estado"
```

La carga devuelve el mismo UUID en `id` y `documento_id`, junto con el campo `estado`. Una respuesta exitosa queda en estado `NORMALIZADO`, con el documento, el texto normalizado y la trazabilidad persistidos en `datos/almacenamiento/`.

## Almacenamiento de una ERS

El almacenamiento es un repositorio simple sobre el sistema de archivos: no requiere motor de base de datos y lo guardado puede inspeccionarse con un editor de texto.

```python
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.persistencia_y_trazabilidad import RepositorioEnArchivos
from etica_ia_ers.procesamiento_textual_y_nlp import NormalizadorDeTexto

repositorio = RepositorioEnArchivos("datos/almacenamiento")

documento = cargar_documento_desde_ruta("datos/entrada/ers.txt")
registro = repositorio.guardar(documento)

texto_normalizado = NormalizadorDeTexto().normalizar(documento.contenido_extraido)
repositorio.guardar_texto_normalizado(registro.id, texto_normalizado)

for resumen in repositorio.listar():
    print(resumen.nombre_original, resumen.estado.value)

print(repositorio.obtener_texto_normalizado(registro.id).normalizado)
```

Operaciones disponibles: `guardar`, `obtener`, `listar`, `buscar_por_hash`, `actualizar_estado`, `guardar_texto_normalizado`, `obtener_texto_normalizado` y `eliminar`. `listar` y `buscar_por_hash` devuelven resúmenes sin el texto de la ERS; `obtener` devuelve el documento completo. `buscar_por_hash` permite detectar que un archivo ya fue cargado antes de volver a analizarlo.

Los estados posibles son `CARGADO`, `NORMALIZADO`, `EVALUADO` y `ERROR`, y acompañan al flujo entrada → NLP → motor → salida. `guardar_texto_normalizado` deja el documento en `NORMALIZADO`; el resto de las transiciones se hacen con `actualizar_estado`.

Guardar una normalización exige que su texto original sea el contenido extraído de ese documento; si no coincide se rechaza con `TextoNormalizadoInvalidoError`, para que lo almacenado no mezcle el texto de una ERS con la normalización de otra.

`RepositorioEnMemoria` implementa el mismo contrato (`RepositorioDeDocumentos`) sin escribir en disco y se utiliza en las pruebas. La API usa `RepositorioEnArchivos` por defecto.

### Qué queda escrito

```text
datos/almacenamiento/
├── documentos/
│   └── <id>/
│       ├── documento.json        # nombre, formato, hash, fechas, estado y metadatos
│       ├── contenido.txt         # texto extraído, tal cual lo devolvió el cargador
│       ├── normalizacion.json    # pasos de normalización aplicados y su fecha
│       └── texto_normalizado.txt # texto ya normalizado, insumo del NLP
└── trazabilidad.jsonl            # un evento por línea: CARGA, NORMALIZACION,
                                  # CAMBIO_ESTADO, ELIMINACION
```

Los dos últimos archivos aparecen recién cuando se guarda una normalización. Cada archivo se escribe de forma atómica y los JSON incluyen `version_formato`, para poder migrar el formato más adelante. La bitácora es de sólo agregado y se consulta con `repositorio.trazabilidad.eventos(id_documento)`.

El contenido de `datos/almacenamiento/` está ignorado por Git: son datos de trabajo, no parte del código.

## Pruebas

Las pruebas generan en memoria documentos TXT, PDF y DOCX mínimos. También construyen entradas vacías, corruptas o sin texto para verificar los errores esperados; no utilizan documentos externos ni archivos del material académico.

Las del almacenamiento se ejecutan contra las dos implementaciones del repositorio y escriben en directorios temporales, nunca en `datos/`.

La prueba del pipeline NLP (`prueba_nlp_ers_ejemplo.py`) es la única que lee archivos del repositorio: las ERS de ejemplo versionadas en `ejemplos/ers/`.

GitHub Actions ejecuta esta misma suite automáticamente en cada pull request hacia `main` y después de cada cambio fusionado en `main`.

```bash
python3 -m pytest
```

## Estructura

```text
configuracion/
├── .gitkeep
└── guardrails/
    └── .gitkeep
datos/
├── entrada/
│   └── .gitkeep
├── salida/
│   └── .gitkeep
└── almacenamiento/
    └── .gitkeep
codigo_fuente/
└── etica_ia_ers/
    ├── configuracion/
    ├── dominio/
    │   ├── anotacion_nlp.py
    │   ├── clasificacion_fragmento.py
    │   ├── documento.py
    │   ├── evaluacion_etica.py
    │   ├── fragmento.py
    │   ├── guardrail.py
    │   ├── registro_documento.py
    │   ├── texto_normalizado.py
    │   └── trazabilidad.py
    ├── entrada_documental/
    │   ├── cargador.py
    │   └── errores.py
    ├── procesamiento_textual_y_nlp/
    │   ├── clasificador.py
    │   ├── detector_ambiguedades.py
    │   ├── errores.py
    │   ├── extractor_elementos.py
    │   ├── normalizador.py
    │   ├── pipeline.py
    │   └── segmentador.py
    ├── modelo_etico_y_guardrails/
    │   ├── errores.py
    │   └── repositorio.py
    ├── evaluacion_documental/
    │   ├── errores.py
    │   └── motor.py
    ├── rubrica_y_agregacion/
    ├── recomendaciones/
    ├── resultados_y_presentacion/
    └── persistencia_y_trazabilidad/
        ├── errores.py
        ├── repositorio.py
        ├── repositorio_archivos.py
        ├── serializacion.py
        └── trazabilidad.py
ejemplos/
├── HALLAZGOS-nlp.md
├── analizar_ers.py
└── ers/
    ├── diagnostico_medico.txt
    ├── scoring_crediticio.txt
    └── sistema_recomendador.txt
pruebas/
├── prueba_api_documentos.py
├── prueba_almacenamiento.py
├── prueba_cargador_documentos.py
├── prueba_clasificador.py
├── prueba_detector_ambiguedades.py
├── prueba_extractor_elementos.py
├── prueba_motor_evaluacion_etica.py
├── prueba_nlp_ers_ejemplo.py
├── prueba_normalizador.py
└── prueba_segmentador.py
```
