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

El prototipo permite cargar documentos ERS, extraer y normalizar su contenido textual, segmentarlo, clasificar sus fragmentos e identificar actores, acciones, condiciones, términos vagos y expresiones ambiguas. También almacena los documentos y su normalización junto con el estado del análisis y una bitácora de trazabilidad.

La carga soporta archivos TXT con codificación UTF-8, PDF con capa de texto y DOCX. El endpoint inicial ejecuta carga, normalización y almacenamiento antes de informar el estado. Todavía no implementa OCR ni el motor de evaluación ética.

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

Las reglas normalizan mayúsculas y acentos sólo para buscar señales; no modifican el texto ni los offsets del fragmento. La clasificación tampoco asigna niveles éticos `Ausente`, `Parcial` o `Explícito`: esa decisión corresponde al futuro motor de evaluación.

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
    │   ├── fragmento.py
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
    │   └── segmentador.py
    ├── modelo_etico_y_guardrails/
    ├── evaluacion_documental/
    ├── rubrica_y_agregacion/
    ├── recomendaciones/
    ├── resultados_y_presentacion/
    └── persistencia_y_trazabilidad/
        ├── errores.py
        ├── repositorio.py
        ├── repositorio_archivos.py
        ├── serializacion.py
        └── trazabilidad.py
pruebas/
├── prueba_api_documentos.py
├── prueba_almacenamiento.py
├── prueba_cargador_documentos.py
├── prueba_clasificador.py
├── prueba_detector_ambiguedades.py
├── prueba_extractor_elementos.py
├── prueba_normalizador.py
└── prueba_segmentador.py
```
