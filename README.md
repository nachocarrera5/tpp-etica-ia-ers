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

Esta base corresponde al Sprint 6 del proyecto. Actualmente permite cargar documentos ERS, extraer y normalizar su contenido textual, y almacenar ambos junto con el estado del análisis y una bitácora de trazabilidad.

La carga soporta archivos TXT con codificación UTF-8, PDF con capa de texto y DOCX. Todavía no implementa OCR, segmentación, motor de evaluación ni endpoints.

## Instalación para desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

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

`RepositorioEnMemoria` implementa el mismo contrato (`RepositorioDeDocumentos`) sin escribir en disco, para pruebas y para desarrollar el endpoint de carga y estado.

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
    │   ├── documento.py
    │   ├── registro_documento.py
    │   ├── texto_normalizado.py
    │   └── trazabilidad.py
    ├── entrada_documental/
    │   ├── cargador.py
    │   └── errores.py
    ├── procesamiento_textual_y_nlp/
    │   ├── errores.py
    │   └── normalizador.py
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
├── prueba_almacenamiento.py
├── prueba_cargador_documentos.py
└── prueba_normalizador.py
```
