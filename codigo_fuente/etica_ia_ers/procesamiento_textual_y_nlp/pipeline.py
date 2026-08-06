"""Punto de entrada del pipeline NLP: normalizar, segmentar y clasificar.

Encadena los pasos ya existentes (SCRUM-96, SCRUM-99 y SCRUM-100) en una sola
llamada, para tener una representacion unica de "lo que produce el NLP" sobre
un texto de ERS. Es el insumo que consumira el motor de evaluacion del Sprint 8.
"""

from __future__ import annotations

from typing import List, Optional

from etica_ia_ers.dominio import FragmentoClasificado

from .clasificador import clasificar_fragmentos
from .normalizador import NormalizadorDeTexto
from .segmentador import segmentar


def analizar_texto(
    texto: str,
    normalizador: Optional[NormalizadorDeTexto] = None,
) -> List[FragmentoClasificado]:
    """Devuelve los fragmentos clasificados de un texto de ERS ya extraido.

    El texto se normaliza, se segmenta en fragmentos y cada fragmento se
    clasifica con reglas trazables. Es equivalente a encadenar a mano
    ``NormalizadorDeTexto().normalizar``, ``segmentar`` y
    ``clasificar_fragmentos``.
    """
    normalizador = normalizador or NormalizadorDeTexto()
    texto_normalizado = normalizador.normalizar(texto)
    fragmentos = segmentar(texto_normalizado.normalizado)
    return clasificar_fragmentos(fragmentos)
