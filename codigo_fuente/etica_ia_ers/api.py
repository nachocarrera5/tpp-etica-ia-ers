import json
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from pydantic import BaseModel, Field
from starlette import status

from etica_ia_ers.dominio import (
    DimensionEtica,
    EstadoAnalisis,
    FamiliaGuardrail,
    FormatoDocumento,
    NivelCobertura,
    PrioridadDocumental,
    SolicitudEvaluacionEtica,
    TipoVinculoEvidencia,
)
from etica_ia_ers.entrada_documental import (
    DocumentoIlegibleError,
    DocumentoVacioError,
    FormatoNoSoportadoError,
    cargar_documento,
)
from etica_ia_ers.evaluacion_documental import (
    ErrorEvaluacionEtica,
    MotorEvaluacionEtica,
)
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_ACTIVOS,
    RepositorioGuardrails,
    RepositorioGuardrailsEnMemoria,
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
    ErrorProcesamientoNLP,
    NormalizadorDeTexto,
    analizar_texto,
)
from etica_ia_ers.resultados_y_presentacion import (
    ErrorExportacion,
    FormatoExportacion,
    FormatoExportacionNoSoportadoError,
    exportar_reporte,
    formatos_disponibles,
    obtener_resultado_documento,
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


class EvidenciaHallazgoResponse(BaseModel):
    fragmento_id: UUID
    identificador_ers: Optional[str] = None
    seccion_origen: Optional[str] = None
    texto: str
    posicion_inicio: Optional[int] = None
    posicion_fin: Optional[int] = None
    tipo_vinculo: TipoVinculoEvidencia
    relevancia: Optional[float] = None
    observacion: Optional[str] = None


class HallazgoResponse(BaseModel):
    hallazgo_id: UUID
    analisis_id: UUID
    guardrail_codigo: str
    guardrail_version: int
    familia_guardrail: FamiliaGuardrail
    dimensiones_asociadas: Tuple[DimensionEtica, ...]
    criterios_asociados: Tuple[str, ...]
    nivel_preliminar: NivelCobertura
    valor_auxiliar: int
    prioridad_documental: PrioridadDocumental
    justificacion: str
    justificacion_prioridad: str
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str] = None
    evidencias: List[EvidenciaHallazgoResponse]
    fecha_generacion: datetime


class ResultadoDimensionResponse(BaseModel):
    dimension_codigo: DimensionEtica
    dimension_nombre: str
    grupo_tematico: str
    nivel_consolidado: NivelCobertura
    valor_auxiliar: int
    prioridad_documental: PrioridadDocumental
    justificacion: str
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str] = None
    brechas_principales: Tuple[str, ...]
    hallazgos_relacionados: Tuple[UUID, ...]


class IndicadoresPorGrupoResponse(BaseModel):
    grupo_tematico: str
    dimensiones_incluidas: Tuple[DimensionEtica, ...]
    ausentes: int
    parciales: int
    explicitas: int
    prioridad_maxima: PrioridadDocumental
    requiere_revision_humana: bool


class IndicadoresGlobalesResponse(BaseModel):
    total_dimensiones: int
    dimensiones_ausentes: int
    dimensiones_parciales: int
    dimensiones_explicitas: int
    porcentaje_cobertura_explicita: float
    porcentaje_cobertura_no_ausente: float
    total_hallazgos: int
    hallazgos_con_revision_humana: int
    porcentaje_revision_humana: float
    hallazgos_prioridad_alta: int
    hallazgos_prioridad_media: int
    hallazgos_prioridad_baja: int
    dimensiones_prioridad_alta: Tuple[DimensionEtica, ...]
    guardrails_aplicados: int
    guardrails_no_aplicables: int
    guardrails_con_error: int
    familias_guardrail_cubiertas: Tuple[FamiliaGuardrail, ...]
    por_grupo: Tuple[IndicadoresPorGrupoResponse, ...]


class MetadatosAnalisisResponse(BaseModel):
    analisis_id: UUID
    documento_id: UUID
    nombre_documento: str
    fecha_inicio: str
    fecha_fin: str
    estado: EstadoAnalisis


class ResultadoAnalisisResponse(BaseModel):
    metadatos: MetadatosAnalisisResponse
    resumen_ejecutivo: str
    lectura_global: str
    indicadores: IndicadoresGlobalesResponse
    resultados_dimension: Tuple[ResultadoDimensionResponse, ...]
    hallazgos: Tuple[HallazgoResponse, ...]
    advertencias: Tuple[str, ...]


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
    return RepositorioEnArchivos()


@lru_cache(maxsize=1)
def obtener_repositorio_guardrails() -> RepositorioGuardrails:
    return RepositorioGuardrailsEnMemoria(GUARDRAILS_ACTIVOS)


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


def _generar_reporte(
    documento_id: UUID,
    repositorio: RepositorioDeDocumentos,
    guardrails: RepositorioGuardrails,
) -> Dict[str, Any]:
    """Ejecuta NLP y motor sobre la ERS almacenada y arma el reporte de resultados.

    Lo comparten la consulta de resultados y la exportacion, para que el archivo
    exportado y la respuesta JSON describan siempre el mismo analisis.
    """
    try:
        registro = repositorio.obtener(documento_id)
    except DocumentoNoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado.",
        ) from error
    except ErrorAlmacenamiento as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el documento.",
        ) from error

    try:
        resultado_nlp = analizar_texto(registro.documento.contenido_extraido)
    except (ErrorNormalizacion, ErrorProcesamientoNLP) as error:
        _marcar_error(repositorio, documento_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensaje": "No se pudo analizar el documento para evaluarlo.",
                "documento_id": str(documento_id),
            },
        ) from error

    solicitud = SolicitudEvaluacionEtica(
        documento_id=documento_id,
        resultado_nlp=resultado_nlp,
        metadatos=registro.documento.metadatos,
    )

    try:
        resultado_evaluacion = MotorEvaluacionEtica(guardrails).evaluar(solicitud)
    except ErrorEvaluacionEtica as error:
        _marcar_error(repositorio, documento_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensaje": "No se pudo evaluar el documento.",
                "documento_id": str(documento_id),
            },
        ) from error

    try:
        repositorio.actualizar_estado(documento_id, EstadoAnalisis.EVALUADO)
    except ErrorAlmacenamiento:
        pass

    return obtener_resultado_documento(
        evaluacion=resultado_evaluacion,
        nombre_documento=registro.documento.nombre_original,
    )


@app.get(
    "/documentos/{documento_id}/resultados",
    response_model=ResultadoAnalisisResponse,
)
def resultados_documento(
    documento_id: UUID,
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
    guardrails: RepositorioGuardrails = Depends(obtener_repositorio_guardrails),
) -> Dict[str, Any]:
    return _generar_reporte(documento_id, repositorio, guardrails)


@app.get(
    "/documentos/{documento_id}/reporte",
    response_class=Response,
    responses={
        200: {
            "description": (
                "Reporte de cobertura etica documental como archivo descargable."
            ),
            "content": {
                "application/json": {},
                "text/markdown": {},
                "text/html": {},
            },
        }
    },
)
def exportar_reporte_documento(
    documento_id: UUID,
    formato: str = Query(
        "json",
        description=(
            "Formato de exportacion. Valores aceptados: "
            + ", ".join(formatos_disponibles())
            + "."
        ),
    ),
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
    guardrails: RepositorioGuardrails = Depends(obtener_repositorio_guardrails),
) -> Response:
    # El formato se resuelve antes de evaluar: un pedido invalido no deberia
    # costar una corrida completa de NLP y motor.
    try:
        formato_exportacion = FormatoExportacion.desde_texto(formato)
    except FormatoExportacionNoSoportadoError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    reporte = _generar_reporte(documento_id, repositorio, guardrails)

    try:
        reporte_exportado = exportar_reporte(reporte, formato_exportacion)
    except ErrorExportacion as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensaje": "No se pudo exportar el reporte del documento.",
                "documento_id": str(documento_id),
            },
        ) from error

    # El nombre lo construye el exportador a partir de un slug ASCII, de modo
    # que el encabezado no puede contener saltos de linea ni comillas.
    return Response(
        content=reporte_exportado.bytes_contenido,
        media_type=reporte_exportado.tipo_contenido,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{reporte_exportado.nombre_archivo}"'
            )
        },
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
