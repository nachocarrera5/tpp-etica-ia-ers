"""Contratos y entidades de dominio."""
from .anotacion_nlp import AnotacionNLP, TipoSenalNLP
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
    "DocumentoERS",
    "EstadoAnalisis",
    "EventoTrazabilidad",
    "FragmentoClasificado",
    "FormatoDocumento",
    "RegistroDocumento",
    "ResultadoAnalisisNLP",
    "ResumenDocumento",
    "TextoNormalizado",
    "TipoClasificacionFragmento",
    "FragmentoDocumental",
    "TipoFragmento",
    "TipoSenalNLP",
]
