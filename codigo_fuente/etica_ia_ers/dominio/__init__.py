"""Contratos y entidades de dominio."""
from .anotacion_nlp import AnotacionNLP, TipoSenalNLP
from .alertas_y_recomendaciones import (
    AlertaDocumental,
    RecomendacionDocumental,
    ResultadoAlertasYRecomendaciones,
    TipoMejora,
)
from .cobertura_etica import (
    GrupoTematico,
    IndicadoresGlobales,
    IndicadoresGrupoTematico,
    IndicadoresGuardrails,
    IndicadoresPrioridad,
    ResultadoCoberturaEtica,
    ResultadoDimensionEtica,
)
from .dominio_aplicacion import DominioAplicacion, resolver_dominio_aplicacion
from .evaluacion_etica import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    EvaluacionPreliminarGuardrail,
    EvidenciaHallazgo,
    HallazgoEvaluacion,
    ReferenciaEvidencia,
    ResultadoAplicacionGuardrail,
    ResultadoEvaluacionEtica,
    SolicitudEvaluacionEtica,
)
from .guardrail import (
    DefinicionGuardrail,
    DimensionEtica,
    EstadoAplicacionGuardrail,
    EstadoGuardrail,
    FamiliaGuardrail,
    IdentidadGuardrailVersionada,
    NivelCobertura,
    PESO_POR_PRIORIDAD,
    PrioridadDocumental,
    TipoVinculoEvidencia,
)
from .clasificacion_fragmento import (
    FragmentoClasificado,
    TipoClasificacionFragmento,
)
from .documento import DocumentoERS, FormatoDocumento
from .registro_documento import EstadoAnalisis, RegistroDocumento, ResumenDocumento
from .resultado_analisis_nlp import ResultadoAnalisisNLP
from .texto_normalizado import TextoNormalizado
from .trazabilidad import AccionTrazabilidad, EventoTrazabilidad
from .fragmento import FragmentoDocumental, TipoFragmento

__all__ = [
    "AccionTrazabilidad",
    "AlertaDocumental",
    "AnotacionNLP",
    "ContextoEvaluacionEtica",
    "DecisionAplicabilidad",
    "DefinicionGuardrail",
    "DimensionEtica",
    "DocumentoERS",
    "DominioAplicacion",
    "EstadoAnalisis",
    "EstadoAplicacionGuardrail",
    "EstadoGuardrail",
    "EvaluacionPreliminarGuardrail",
    "EvidenciaHallazgo",
    "EventoTrazabilidad",
    "FragmentoClasificado",
    "FamiliaGuardrail",
    "FormatoDocumento",
    "GrupoTematico",
    "HallazgoEvaluacion",
    "IdentidadGuardrailVersionada",
    "IndicadoresGlobales",
    "IndicadoresGrupoTematico",
    "IndicadoresGuardrails",
    "IndicadoresPrioridad",
    "NivelCobertura",
    "PESO_POR_PRIORIDAD",
    "PrioridadDocumental",
    "ReferenciaEvidencia",
    "RecomendacionDocumental",
    "RegistroDocumento",
    "ResultadoAnalisisNLP",
    "ResultadoAplicacionGuardrail",
    "ResultadoAlertasYRecomendaciones",
    "ResultadoCoberturaEtica",
    "ResultadoDimensionEtica",
    "ResultadoEvaluacionEtica",
    "ResumenDocumento",
    "SolicitudEvaluacionEtica",
    "TextoNormalizado",
    "TipoClasificacionFragmento",
    "FragmentoDocumental",
    "TipoFragmento",
    "TipoMejora",
    "TipoSenalNLP",
    "TipoVinculoEvidencia",
    "resolver_dominio_aplicacion",
]
