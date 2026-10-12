import json
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
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
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from etica_ia_ers.dominio import (
    DimensionEtica,
    DocumentoERS,
    DominioAplicacion,
    EstadoAnalisis,
    FamiliaGuardrail,
    FormatoDocumento,
    NivelCobertura,
    PrioridadDocumental,
    SolicitudEvaluacionEtica,
    TipoMejora,
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


class ConfiguracionPublicaResponse(BaseModel):
    modo_publico: bool
    persistencia_habilitada: bool
    tamano_maximo_mb: float
    formatos_soportados: Tuple[FormatoDocumento, ...]


class ResumenDocumentoResponse(BaseModel):
    documento_id: UUID
    nombre_original: str
    formato_origen: FormatoDocumento
    estado: EstadoAnalisis
    fecha_carga: datetime
    fecha_actualizacion: datetime
    metadatos: Dict[str, Any] = Field(default_factory=dict)


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
    fragmentos_clave: Tuple[str, ...] = ()


class HallazgoResponse(BaseModel):
    hallazgo_id: UUID
    analisis_id: UUID
    guardrail_codigo: str
    guardrail_version: int
    guardrail_nombre: Optional[str] = None
    guardrail_descripcion: Optional[str] = None
    familia_guardrail: FamiliaGuardrail
    dimensiones_asociadas: Tuple[DimensionEtica, ...]
    criterios_asociados: Tuple[str, ...]
    nivel_preliminar: NivelCobertura
    valor_auxiliar: int
    prioridad_documental: PrioridadDocumental
    peso: float = 1.0
    justificacion: str
    justificacion_prioridad: str
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str] = None
    evidencias: List[EvidenciaHallazgoResponse]
    fecha_generacion: datetime


class ResultadoDimensionResponse(BaseModel):
    resultado_dimension_id: Optional[UUID] = None
    dimension_codigo: DimensionEtica
    dimension_nombre: str
    grupo_tematico: str
    nivel_consolidado: Optional[NivelCobertura] = None
    valor_auxiliar: Optional[int] = None
    prioridad_documental: Optional[PrioridadDocumental] = None
    justificacion: str
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str] = None
    brechas_principales: Tuple[str, ...]
    hallazgos_relacionados: Tuple[UUID, ...]
    porcentaje_cobertura_ponderada: Optional[float] = None
    guardrails_criticos_pendientes: Tuple[str, ...] = ()


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
    porcentaje_cobertura_ponderada: float = 0.0
    total_hallazgos: int
    total_alertas: int
    total_recomendaciones: int
    recomendaciones_alta_prioridad: int
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
    dominio_declarado: Optional[str] = None
    dominio_aplicacion: Optional[DominioAplicacion] = None


class AlertaDocumentalResponse(BaseModel):
    alerta_id: UUID
    analisis_id: UUID
    documento_id: UUID
    resultado_dimension_id: UUID
    dimension_codigo: DimensionEtica
    nivel_cobertura: NivelCobertura
    prioridad_documental: PrioridadDocumental
    titulo: str
    descripcion: str
    brechas: Tuple[str, ...]
    hallazgos_relacionados: Tuple[UUID, ...]
    recomendaciones_asociadas: Tuple[UUID, ...]
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str] = None


class RecomendacionDocumentalResponse(BaseModel):
    recomendacion_id: UUID
    analisis_id: UUID
    resultado_dimension_id: UUID
    dimension_codigo: DimensionEtica
    hallazgos_relacionados: Tuple[UUID, ...]
    accion_sugerida: str
    fundamento: str
    prioridad_documental: PrioridadDocumental
    tipo_mejora: TipoMejora
    plantilla_version: str


class ResultadoAnalisisResponse(BaseModel):
    metadatos: MetadatosAnalisisResponse
    resumen_ejecutivo: str
    lectura_global: str
    indicadores: IndicadoresGlobalesResponse
    resultados_dimension: Tuple[ResultadoDimensionResponse, ...]
    hallazgos: Tuple[HallazgoResponse, ...]
    alertas: Tuple[AlertaDocumentalResponse, ...]
    recomendaciones: Tuple[RecomendacionDocumentalResponse, ...]
    advertencias: Tuple[str, ...]


app = FastAPI(
    title="Revisión ética temprana de ERS de IA",
    version="0.1.0",
    description=(
        "Aplicación para cargar ERS, analizar su texto y revisar cobertura "
        "ética documental preliminar."
    ),
)

_DIRECTORIO_INTERFAZ = Path(__file__).parent / "interfaz_web"
app.mount(
    "/recursos",
    StaticFiles(directory=_DIRECTORIO_INTERFAZ),
    name="recursos",
)


@lru_cache(maxsize=1)
def obtener_repositorio() -> RepositorioDeDocumentos:
    _exigir_modo_local()
    return RepositorioEnArchivos()


@lru_cache(maxsize=1)
def obtener_repositorio_guardrails() -> RepositorioGuardrails:
    return RepositorioGuardrailsEnMemoria(GUARDRAILS_ACTIVOS)


def es_modo_publico() -> bool:
    return os.getenv("MODO_PUBLICO", "false").strip().lower() in {
        "1",
        "si",
        "true",
        "yes",
    }


def tamano_maximo_archivo_mb() -> float:
    valor = os.getenv("MAX_TAMANO_ARCHIVO_MB", "10")
    try:
        return max(float(valor), 0.01)
    except ValueError:
        return 10.0


def _exigir_modo_local() -> None:
    if es_modo_publico():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La operación no está disponible en la demo pública.",
        )


async def _leer_archivo(archivo: UploadFile) -> bytes:
    limite = int(tamano_maximo_archivo_mb() * 1024 * 1024)
    contenido = await archivo.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                "El archivo supera el tamaño máximo permitido de "
                f"{tamano_maximo_archivo_mb():g} MB."
            ),
        )
    return contenido


@app.get("/", include_in_schema=False, response_class=FileResponse)
def interfaz_web() -> FileResponse:
    return FileResponse(_DIRECTORIO_INTERFAZ / "index.html")


@app.get("/salud", tags=["operación"])
def salud() -> Dict[str, str]:
    return {"estado": "disponible", "version": app.version}


@app.get(
    "/configuracion-publica",
    response_model=ConfiguracionPublicaResponse,
    tags=["operación"],
)
def configuracion_publica() -> ConfiguracionPublicaResponse:
    modo_publico = es_modo_publico()
    return ConfiguracionPublicaResponse(
        modo_publico=modo_publico,
        persistencia_habilitada=not modo_publico,
        tamano_maximo_mb=tamano_maximo_archivo_mb(),
        formatos_soportados=tuple(FormatoDocumento),
    )


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
    _exigir_modo_local()
    metadatos_dict = _parsear_metadatos(metadatos)

    try:
        contenido = await _leer_archivo(archivo)
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


@app.post(
    "/analisis",
    response_model=ResultadoAnalisisResponse,
    tags=["análisis público"],
)
async def analizar_documento_endpoint(
    archivo: UploadFile = File(...),
    metadatos: Optional[str] = Form(None),
    guardrails: RepositorioGuardrails = Depends(obtener_repositorio_guardrails),
) -> ResultadoAnalisisResponse:
    metadatos_dict = _parsear_metadatos(metadatos)
    try:
        contenido = await _leer_archivo(archivo)
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

    return _analizar_y_evaluar(documento, guardrails)


@app.get(
    "/documentos",
    response_model=List[ResumenDocumentoResponse],
)
def listar_documentos(
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
) -> List[ResumenDocumentoResponse]:
    _exigir_modo_local()
    try:
        resumenes = repositorio.listar()
    except ErrorAlmacenamiento as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron listar los documentos.",
        ) from error

    return [
        ResumenDocumentoResponse(
            documento_id=resumen.id,
            nombre_original=resumen.nombre_original,
            formato_origen=resumen.formato_origen,
            estado=resumen.estado,
            fecha_carga=resumen.fecha_carga,
            fecha_actualizacion=resumen.fecha_actualizacion,
            metadatos=resumen.metadatos,
        )
        for resumen in reversed(resumenes)
    ]


@app.get(
    "/documentos/{documento_id}/estado",
    response_model=EstadoDocumentoResponse,
)
def estado_documento(
    documento_id: UUID,
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
) -> EstadoDocumentoResponse:
    _exigir_modo_local()
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
    _exigir_modo_local()
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
        resultado = _analizar_y_evaluar(registro.documento, guardrails)
    except HTTPException:
        _marcar_error(repositorio, documento_id)
        raise

    try:
        repositorio.actualizar_estado(documento_id, EstadoAnalisis.EVALUADO)
    except ErrorAlmacenamiento:
        pass

    return resultado


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
    return _respuesta_reporte_exportado(
        reporte,
        formato_exportacion,
        documento_id,
    )


@app.post(
    "/reporte",
    response_class=Response,
    responses={
        200: {
            "description": (
                "Reporte del análisis recibido como archivo descargable."
            ),
            "content": {
                "application/json": {},
                "text/markdown": {},
                "text/html": {},
            },
        }
    },
    tags=["análisis público"],
)
def exportar_resultado_analisis(
    reporte: ResultadoAnalisisResponse,
    formato: str = Query(
        "json",
        description=(
            "Formato de exportacion. Valores aceptados: "
            + ", ".join(formatos_disponibles())
            + "."
        ),
    ),
) -> Response:
    """Exporta un resultado ya calculado sin reevaluar ni persistir la ERS."""
    try:
        formato_exportacion = FormatoExportacion.desde_texto(formato)
    except FormatoExportacionNoSoportadoError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _respuesta_reporte_exportado(
        reporte.model_dump(mode="json"),
        formato_exportacion,
        reporte.metadatos.documento_id,
    )


def _respuesta_reporte_exportado(
    reporte: Dict[str, Any],
    formato: FormatoExportacion,
    documento_id: UUID,
) -> Response:
    """Convierte un resultado validado en una descarga HTTP."""

    try:
        reporte_exportado = exportar_reporte(reporte, formato)
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


@app.delete(
    "/documentos/{documento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_documento(
    documento_id: UUID,
    repositorio: RepositorioDeDocumentos = Depends(obtener_repositorio),
) -> Response:
    _exigir_modo_local()
    try:
        repositorio.eliminar(documento_id)
    except DocumentoNoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado.",
        ) from error
    except ErrorAlmacenamiento as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo eliminar el documento.",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _analizar_y_evaluar(
    documento: DocumentoERS,
    guardrails: RepositorioGuardrails,
) -> ResultadoAnalisisResponse:
    try:
        resultado_nlp = analizar_texto(documento.contenido_extraido)
    except (ErrorNormalizacion, ErrorProcesamientoNLP) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensaje": "No se pudo analizar el documento para evaluarlo.",
                "documento_id": str(documento.id),
            },
        ) from error

    solicitud = SolicitudEvaluacionEtica(
        documento_id=documento.id,
        resultado_nlp=resultado_nlp,
        metadatos=documento.metadatos,
    )
    try:
        resultado_evaluacion = MotorEvaluacionEtica(guardrails).evaluar(solicitud)
    except ErrorEvaluacionEtica as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "mensaje": "No se pudo evaluar el documento.",
                "documento_id": str(documento.id),
            },
        ) from error

    return obtener_resultado_documento(
        evaluacion=resultado_evaluacion,
        nombre_documento=documento.nombre_original,
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
