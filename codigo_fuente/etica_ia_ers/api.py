import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette import status

from etica_ia_ers.dominio import FormatoDocumento
from etica_ia_ers.entrada_documental import (
    DocumentoIlegibleError,
    DocumentoVacioError,
    FormatoNoSoportadoError,
    cargar_documento,
)

# Estados del análisis
class EstadoAnalisis(str, Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADO = "COMPLETADO"
    ERROR = "ERROR"


class DocumentoCargaResponse(BaseModel):
    id: UUID
    documento_id: Optional[UUID] = None
    nombre_original: Optional[str] = None
    formato_origen: Optional[FormatoDocumento] = None
    status: EstadoAnalisis
    fecha_carga: Optional[datetime] = None
    hash_contenido: Optional[str] = None
    metadatos: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class EstadoDocumentoResponse(BaseModel):
    id: UUID
    status: EstadoAnalisis
    fecha_actualizacion: datetime
    error: Optional[str] = None


@dataclass
class _DocumentoCargaState:
    documento_id: Optional[UUID]
    status: EstadoAnalisis
    fecha_actualizacion: datetime
    error: Optional[str] = None
    metadatos: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI(
    title="API de carga de ERS",
    version="0.1.0",
    description="Punto de entrada inicial para cargar documentos ERS y consultar el estado de análisis.",
)

_DOCUMENTOS: Dict[UUID, _DocumentoCargaState] = {}


def _parsear_metadatos(metadatos: Optional[str]) -> Dict[str, Any]:
    if metadatos is None or metadatos.strip() == "":
        return {}
    try:
        valor = json.loads(metadatos)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Metadatos deben ser JSON válido.") from error
    if not isinstance(valor, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Metadatos deben ser un objeto JSON.")
    return valor

# Carga de documentos
@app.post(
    "/documentos",
    response_model=DocumentoCargaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def cargar_documento_endpoint(
    archivo: UploadFile = File(...),
    metadatos: Optional[str] = Form(None),
) -> DocumentoCargaResponse:
    metadatos_dict = _parsear_metadatos(metadatos)
    carga_id = uuid4()
    estado = _DocumentoCargaState(
        documento_id=None,
        status=EstadoAnalisis.PENDIENTE,
        fecha_actualizacion=datetime.now(timezone.utc),
        error=None,
        metadatos=metadatos_dict,
    )
    _DOCUMENTOS[carga_id] = estado

    try:
        contenido = await archivo.read()
        documento = cargar_documento(archivo.filename, contenido, metadatos_dict)
        estado.documento_id = documento.id
        estado.status = EstadoAnalisis.COMPLETADO
        estado.fecha_actualizacion = datetime.now(timezone.utc)

        return DocumentoCargaResponse(
            id=carga_id,
            documento_id=documento.id,
            nombre_original=documento.nombre_original,
            formato_origen=documento.formato_origen,
            status=estado.status,
            fecha_carga=documento.fecha_carga,
            hash_contenido=documento.hash_contenido,
            metadatos=documento.metadatos,
            error=None,
        )
    except (FormatoNoSoportadoError, DocumentoIlegibleError, DocumentoVacioError) as error:
        estado.status = EstadoAnalisis.ERROR
        estado.error = str(error)
        estado.fecha_actualizacion = datetime.now(timezone.utc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        estado.status = EstadoAnalisis.ERROR
        estado.error = "Error interno al procesar el archivo."
        estado.fecha_actualizacion = datetime.now(timezone.utc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

# Consulta del estado del análisis
@app.get(
        "/documentos/{carga_id}/estado",
        response_model=EstadoDocumentoResponse
)
def estado_documento(carga_id: UUID) -> EstadoDocumentoResponse:
    estado = _DOCUMENTOS.get(carga_id)
    if estado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    return EstadoDocumentoResponse(
        id=carga_id,
        status=estado.status,
        fecha_actualizacion=estado.fecha_actualizacion,
        error=estado.error,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "etica_ia_ers.api:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
