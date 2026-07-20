from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Union
from uuid import uuid4

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from etica_ia_ers.domain import DocumentoERS, FormatoDocumento

from .errores import (
    DocumentoIlegibleError,
    DocumentoVacioError,
    FormatoNoSoportadoError,
)

Metadatos = Optional[Dict[str, Any]]
Extractor = Callable[[bytes], str]


def _extraer_txt(contenido: bytes) -> str:
    try:
        return contenido.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DocumentoIlegibleError(
            "El archivo TXT no tiene una codificacion UTF-8 valida."
        ) from error


def _extraer_pdf(contenido: bytes) -> str:
    try:
        lector = PdfReader(BytesIO(contenido))
        if lector.is_encrypted:
            raise DocumentoIlegibleError(
                "El archivo PDF esta cifrado y no puede procesarse."
            )
        return "\n\n".join(pagina.extract_text() or "" for pagina in lector.pages)
    except DocumentoIlegibleError:
        raise
    except Exception as error:
        raise DocumentoIlegibleError(
            "El archivo PDF esta corrupto o no puede leerse."
        ) from error


def _bloques_docx(documento: Any) -> Iterable[Union[Paragraph, Table]]:
    for elemento in documento.element.body.iterchildren():
        if elemento.tag.endswith("}p"):
            yield Paragraph(elemento, documento)
        elif elemento.tag.endswith("}tbl"):
            yield Table(elemento, documento)


def _texto_tabla(tabla: Table) -> str:
    return "\n".join(
        "\t".join(celda.text for celda in fila.cells) for fila in tabla.rows
    )


def _extraer_docx(contenido: bytes) -> str:
    try:
        documento = Document(BytesIO(contenido))
        bloques = []
        for bloque in _bloques_docx(documento):
            if isinstance(bloque, Paragraph):
                bloques.append(bloque.text)
            else:
                bloques.append(_texto_tabla(bloque))
        return "\n\n".join(bloques)
    except Exception as error:
        raise DocumentoIlegibleError(
            "El archivo DOCX esta corrupto o no puede leerse."
        ) from error


_FORMATOS = {
    ".txt": (FormatoDocumento.TXT, _extraer_txt),
    ".pdf": (FormatoDocumento.PDF, _extraer_pdf),
    ".docx": (FormatoDocumento.DOCX, _extraer_docx),
}


def cargar_documento(
    nombre_archivo: str,
    contenido: bytes,
    metadatos: Metadatos = None,
) -> DocumentoERS:
    nombre_original = Path(nombre_archivo).name
    formato_y_extractor = _FORMATOS.get(Path(nombre_original).suffix.lower())
    if formato_y_extractor is None:
        raise FormatoNoSoportadoError(
            "Formato no soportado. Los formatos admitidos son TXT, PDF y DOCX."
        )
    if not contenido:
        raise DocumentoVacioError("El documento esta vacio.")

    formato, extractor = formato_y_extractor
    texto_extraido = extractor(contenido)
    if not texto_extraido.strip():
        if formato is FormatoDocumento.PDF:
            raise DocumentoIlegibleError(
                "El archivo PDF no contiene texto procesable; no se realiza OCR."
            )
        raise DocumentoVacioError(
            "El documento no contiene texto procesable."
        )

    return DocumentoERS(
        id=uuid4(),
        nombre_original=nombre_original,
        formato_origen=formato,
        contenido_extraido=texto_extraido,
        hash_contenido=sha256(contenido).hexdigest(),
        fecha_carga=datetime.now(timezone.utc),
        metadatos=dict(metadatos or {}),
    )


def cargar_documento_desde_ruta(
    ruta: Union[str, Path],
    metadatos: Metadatos = None,
) -> DocumentoERS:
    ruta_documento = Path(ruta)
    return cargar_documento(
        ruta_documento.name,
        ruta_documento.read_bytes(),
        metadatos,
    )
