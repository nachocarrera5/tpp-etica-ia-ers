import json
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette import status

from etica_ia_ers.dominio import EstadoAnalisis, FormatoDocumento
from etica_ia_ers.entrada_documental import (
    DocumentoIlegibleError,
    DocumentoVacioError,
    FormatoNoSoportadoError,
    cargar_documento,
)
from etica_ia_ers.persistencia_y_trazabilidad import (
    DocumentoNoEncontradoError,
    DocumentoYaRegistradoError,
    ErrorAlmacenamiento,
    RepositorioDeDocumentos,
    RepositorioEnArchivos,
)
from etica_ia_ers.procesamiento_textual_y_nlp import (
    ErrorNormalizacion,
    NormalizadorDeTexto,
)


class DocumentoCargaResponse(BaseModel):
    id: UUID
    documento_id: UUID
    nombre_original: str
    formato_origen: FormatoDocumento
    estado: EstadoAnalisis
    fecha_carga: datetime
    hash_contenido: str
    metadatos: Dict[str, Any] = Field(default_factory=dict)


class EstadoDocumentoResponse(BaseModel):
    id: UUID
    estado: EstadoAnalisis
    fecha_actualizacion: datetime


app = FastAPI(
    title="API de carga de ERS",
    version="0.1.0",
    description=(
        "Punto de entrada para cargar, normalizar y almacenar documentos ERS, "
        "y consultar el estado de su analisis."
    ),
)


@lru_cache(maxsize=1)
def obtener_repositorio() -> RepositorioDeDocumentos:
    """Repositorio persistente por defecto; las pruebas pueden reemplazarlo."""
    return RepositorioEnArchivos()


def _parsear_metadatos(metadatos: Optional[str]) -> Dict[str, Any]:
    if metadatos is None or metadatos.strip() == "":
        return {}
    try:
        valor = json.loads(metadatos)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los metadatos deben ser JSON valido.",
        ) from error
    if not isinstance(valor, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los metadatos deben ser un objeto JSON.",
        )
    return valor


@app.post(
    "/documentos",
    response_model=DocumentoCargaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def cargar_documento_endpoint(
    archivo: UploadFile = File(...),
    metadatos: Optional[str] = Form(None),
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
) -> DocumentoCargaResponse:
    metadatos_dict = _parsear_metadatos(metadatos)

    try:
        contenido = await archivo.read()
        documento = cargar_documento(
            archivo.filename or "",
            contenido,
            metadatos_dict,
        )
    except (FormatoNoSoportadoError, DocumentoIlegibleError, DocumentoVacioError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    try:
        repositorio.guardar(documento)
        texto_normalizado = NormalizadorDeTexto().normalizar(
            documento.contenido_extraido
        )
        resumen = repositorio.guardar_texto_normalizado(
            documento.id,
            texto_normalizado,
        )
    except DocumentoYaRegistradoError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except ErrorNormalizacion as error:
        _marcar_error(repositorio, documento.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensaje": "No se pudo normalizar el documento.",
                "documento_id": str(documento.id),
            },
        ) from error
    except ErrorAlmacenamiento as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo almacenar el documento.",
        ) from error

    return DocumentoCargaResponse(
        id=documento.id,
        documento_id=documento.id,
        nombre_original=documento.nombre_original,
        formato_origen=documento.formato_origen,
        estado=resumen.estado,
        fecha_carga=documento.fecha_carga,
        hash_contenido=documento.hash_contenido,
        metadatos=documento.metadatos,
    )


@app.get(
    "/documentos/{documento_id}/estado",
    response_model=EstadoDocumentoResponse,
)
def estado_documento(
    documento_id: UUID,
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
) -> EstadoDocumentoResponse:
    try:
        resumen = repositorio.obtener(documento_id).resumen
    except DocumentoNoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado.",
        ) from error
    except ErrorAlmacenamiento as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo consultar el estado del documento.",
        ) from error

    return EstadoDocumentoResponse(
        id=documento_id,
        estado=resumen.estado,
        fecha_actualizacion=resumen.fecha_actualizacion,
    )


def _marcar_error(
    repositorio: RepositorioDeDocumentos,
    documento_id: UUID,
) -> None:
    try:
        repositorio.actualizar_estado(documento_id, EstadoAnalisis.ERROR)
    except ErrorAlmacenamiento:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "etica_ia_ers.api:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
