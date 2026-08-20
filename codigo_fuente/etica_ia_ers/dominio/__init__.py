"""Contratos y entidades de dominio."""
from .anotacion_nlp import AnotacionNLP, TipoSenalNLP
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
    "AnotacionNLP",
    "ContextoEvaluacionEtica",
    "DecisionAplicabilidad",
    "DefinicionGuardrail",
    "DimensionEtica",
    "DocumentoERS",
    "EstadoAnalisis",
    "EstadoAplicacionGuardrail",
    "EstadoGuardrail",
    "EvaluacionPreliminarGuardrail",
    "EvidenciaHallazgo",
    "EventoTrazabilidad",
    "FragmentoClasificado",
    "FamiliaGuardrail",
    "FormatoDocumento",
    "HallazgoEvaluacion",
    "IdentidadGuardrailVersionada",
    "NivelCobertura",
    "PrioridadDocumental",
    "ReferenciaEvidencia",
    "RegistroDocumento",
    "ResultadoAnalisisNLP",
    "ResultadoAplicacionGuardrail",
    "ResultadoEvaluacionEtica",
    "ResumenDocumento",
    "SolicitudEvaluacionEtica",
    "TextoNormalizado",
    "TipoClasificacionFragmento",
    "FragmentoDocumental",
    "TipoFragmento",
    "TipoSenalNLP",
    "TipoVinculoEvidencia",
]
