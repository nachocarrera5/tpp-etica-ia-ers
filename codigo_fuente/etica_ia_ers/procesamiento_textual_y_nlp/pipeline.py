"""Punto de entrada del pipeline NLP de una ERS.

Encadena normalizacion, segmentacion, clasificacion y extraccion de senales en
una sola llamada. El resultado conserva todos los datos que consumira el motor
de evaluacion.
"""

from __future__ import annotations

from typing import List, Optional

from etica_ia_ers.dominio import AnotacionNLP, ResultadoAnalisisNLP

from .clasificador import clasificar_fragmentos
from .detector_ambiguedades import detectar_ambiguedades_y_terminos_vagos
from .extractor_elementos import extraer_actores_acciones_condiciones
from .normalizador import NormalizadorDeTexto
from .segmentador import segmentar


def analizar_texto(
    texto: str,
    normalizador: Optional[NormalizadorDeTexto] = None,
) -> ResultadoAnalisisNLP:
    """Procesa un texto de ERS ya extraido y devuelve un resultado trazable."""

    normalizador = normalizador or NormalizadorDeTexto()
    texto_normalizado = normalizador.normalizar(texto)
    fragmentos = segmentar(texto_normalizado.normalizado)
    fragmentos_clasificados = clasificar_fragmentos(fragmentos)

    anotaciones: List[AnotacionNLP] = []
    for fragmento in fragmentos:
        senales_fragmento = extraer_actores_acciones_condiciones(fragmento)
        senales_fragmento.extend(
            detectar_ambiguedades_y_terminos_vagos(fragmento)
        )
        anotaciones.extend(
            sorted(
                senales_fragmento,
                key=lambda senal: (
                    senal.posicion_inicio,
                    senal.posicion_fin,
                    senal.tipo_senal.value,
                ),
            )
        )

    return ResultadoAnalisisNLP(
        texto_normalizado=texto_normalizado,
        fragmentos_clasificados=tuple(fragmentos_clasificados),
        anotaciones=tuple(anotaciones),
    )
