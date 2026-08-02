"""Contratos y entidades de dominio."""
from .documento import DocumentoERS, FormatoDocumento
from .registro_documento import EstadoAnalisis, RegistroDocumento, ResumenDocumento
from .texto_normalizado import TextoNormalizado
from .trazabilidad import AccionTrazabilidad, EventoTrazabilidad
from .fragmento import FragmentoDocumental, TipoFragmento

__all__ = [
    "AccionTrazabilidad",
    "DocumentoERS",
    "EstadoAnalisis",
    "EventoTrazabilidad",
    "FormatoDocumento",
    "RegistroDocumento",
    "ResumenDocumento",
    "TextoNormalizado",
    "FragmentoDocumental",
    "TipoFragmento",
]
