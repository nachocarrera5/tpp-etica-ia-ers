from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Pattern, Tuple
from uuid import UUID

from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    DefinicionGuardrail,
    EvaluacionPreliminarGuardrail,
    FragmentoDocumental,
    NivelCobertura,
    ReferenciaEvidencia,
    TipoFragmento,
    TipoVinculoEvidencia,
)


@dataclass(frozen=True)
class SenalLexica:
    nombre: str
    patron: Pattern[str]


@dataclass(frozen=True)
class CoincidenciaSenal:
    nombre: str
    fragmentos_clave: Tuple[str, ...]


def senal(nombre: str, expresion: str) -> SenalLexica:
    return SenalLexica(nombre, re.compile(rf"(?<!\w)(?:{expresion})(?!\w)"))


def _normalizar_para_busqueda_con_mapa(texto: str) -> Tuple[str, Tuple[int, ...]]:
    caracteres: List[str] = []
    posiciones: List[int] = []
    for posicion, caracter_original in enumerate(texto):
        descompuesto = unicodedata.normalize("NFD", caracter_original.casefold())
        sin_acentos = "".join(
            caracter
            for caracter in descompuesto
            if unicodedata.category(caracter) != "Mn"
        )
        for caracter in sin_acentos:
            if caracter.isspace():
                if caracteres and caracteres[-1] != " ":
                    caracteres.append(" ")
                    posiciones.append(posicion)
                continue
            caracteres.append(caracter)
            posiciones.append(posicion)

    if caracteres and caracteres[-1] == " ":
        caracteres.pop()
        posiciones.pop()
    return "".join(caracteres), tuple(posiciones)


def _normalizar_para_busqueda(texto: str) -> str:
    return _normalizar_para_busqueda_con_mapa(texto)[0]


def _acotar_fragmento_clave(fragmento: str) -> Tuple[str, ...]:
    fragmento = fragmento.strip()
    if not fragmento:
        return ()
    if len(fragmento) <= 180:
        return (fragmento,)

    inicio = fragmento[:90].rsplit(" ", 1)[0].strip()
    fin = fragmento[-90:].split(" ", 1)[-1].strip()
    return tuple(parte for parte in (inicio, fin) if parte)


def _fragmentos_evaluables(
    contexto: ContextoEvaluacionEtica,
) -> Tuple[FragmentoDocumental, ...]:
    return tuple(
        clasificado.fragmento
        for clasificado in contexto.resultado_nlp.fragmentos_clasificados
        if clasificado.fragmento.tipo_fragmento != TipoFragmento.ENCABEZADO
    )


def _buscar_coincidencias(
    fragmentos: Tuple[FragmentoDocumental, ...],
    senales: Tuple[SenalLexica, ...],
) -> Dict[UUID, List[CoincidenciaSenal]]:
    coincidencias: Dict[UUID, List[CoincidenciaSenal]] = {}
    for fragmento in fragmentos:
        texto, mapa_posiciones = _normalizar_para_busqueda_con_mapa(
            fragmento.texto
        )
        detectadas: List[CoincidenciaSenal] = []
        for senal_lexica in senales:
            coincidencia = senal_lexica.patron.search(texto)
            if coincidencia is None:
                continue
            inicio, fin = coincidencia.span()
            if inicio == fin or not mapa_posiciones:
                fragmentos_clave = ()
            else:
                inicio_original = mapa_posiciones[inicio]
                fin_original = mapa_posiciones[fin - 1] + 1
                fragmentos_clave = _acotar_fragmento_clave(
                    fragmento.texto[inicio_original:fin_original]
                )
            detectadas.append(
                CoincidenciaSenal(senal_lexica.nombre, fragmentos_clave)
            )
        if detectadas:
            coincidencias[fragmento.id] = detectadas
    return coincidencias


def _crear_evidencias(
    coincidencias: Dict[UUID, List[CoincidenciaSenal]],
    tipo_vinculo: TipoVinculoEvidencia,
) -> Tuple[ReferenciaEvidencia, ...]:
    return tuple(
        ReferenciaEvidencia(
            fragmento_id=fragmento_id,
            tipo_vinculo=tipo_vinculo,
            observacion="Senales detectadas: "
            + ", ".join(
                sorted({coincidencia.nombre for coincidencia in detectadas})
            ),
            fragmentos_clave=tuple(
                dict.fromkeys(
                    fragmento_clave
                    for coincidencia in detectadas
                    for fragmento_clave in coincidencia.fragmentos_clave
                )
            ),
        )
        for fragmento_id, detectadas in coincidencias.items()
    )


@dataclass(frozen=True)
class GuardrailLexico:
    definicion: DefinicionGuardrail
    senales_explicitas: Tuple[SenalLexica, ...] = ()
    senales_parciales: Tuple[SenalLexica, ...] = ()

    def decidir_aplicabilidad(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> DecisionAplicabilidad:
        if not self.definicion.aplica_a_dominio(contexto.dominio_aplicacion):
            dominios = ", ".join(
                dominio.value for dominio in self.definicion.dominios
            )
            return DecisionAplicabilidad(
                aplica=False,
                motivo=(
                    "El guardrail es especifico del dominio "
                    f"{dominios} y la ERS no declara ese dominio."
                ),
            )

        fragmentos = _fragmentos_evaluables(contexto)
        if not fragmentos:
            return DecisionAplicabilidad(
                aplica=False,
                motivo=(
                    "El documento no contiene fragmentos evaluables "
                    "distintos de encabezados."
                ),
            )
        return DecisionAplicabilidad(
            aplica=True,
            motivo="El documento contiene fragmentos evaluables para la dimension.",
        )

    def evaluar(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> EvaluacionPreliminarGuardrail:
        fragmentos = _fragmentos_evaluables(contexto)

        explicitas = _buscar_coincidencias(fragmentos, self.senales_explicitas)
        if explicitas:
            nombres = sorted(
                {
                    coincidencia.nombre
                    for lista in explicitas.values()
                    for coincidencia in lista
                }
            )
            return EvaluacionPreliminarGuardrail(
                nivel=NivelCobertura.EXPLICITO,
                justificacion=(
                    "Se hallo evidencia documental clara y localizada: "
                    + ", ".join(nombres)
                    + "."
                ),
                prioridad=self.definicion.prioridad_base,
                justificacion_prioridad=(
                    "La prioridad responde a la criticidad documental "
                    "definida para el guardrail y es independiente del nivel."
                ),
                evidencias=_crear_evidencias(
                    explicitas,
                    TipoVinculoEvidencia.SOPORTA,
                ),
                requiere_revision_humana=True,
                motivo_revision_humana=(
                    "Un nivel Explicito no certifica la adecuacion real del "
                    "sistema; requiere revision humana."
                ),
            )

        parciales = _buscar_coincidencias(fragmentos, self.senales_parciales)
        if parciales:
            nombres = sorted(
                {
                    coincidencia.nombre
                    for lista in parciales.values()
                    for coincidencia in lista
                }
            )
            return EvaluacionPreliminarGuardrail(
                nivel=NivelCobertura.PARCIAL,
                justificacion=(
                    "Se hallo evidencia generica, incompleta o ambigua: "
                    + ", ".join(nombres)
                    + "."
                ),
                prioridad=self.definicion.prioridad_base,
                justificacion_prioridad=(
                    "La prioridad responde a la criticidad documental "
                    "definida para el guardrail y es independiente del nivel."
                ),
                evidencias=_crear_evidencias(
                    parciales,
                    TipoVinculoEvidencia.CONTEXTUALIZA,
                ),
                requiere_revision_humana=True,
                motivo_revision_humana=(
                    "La evidencia parcial requiere revision humana para "
                    "completar o verificar la especificacion."
                ),
            )

        return EvaluacionPreliminarGuardrail(
            nivel=NivelCobertura.AUSENTE,
            justificacion=(
                "No se hallo evidencia documental relevante para este "
                "guardrail."
            ),
            prioridad=self.definicion.prioridad_base,
            justificacion_prioridad=(
                "La prioridad responde a la criticidad documental "
                "definida para el guardrail y es independiente del nivel."
            ),
            evidencias=(),
            requiere_revision_humana=True,
            motivo_revision_humana=(
                "La ausencia de evidencia debe confirmarse con el "
                "responsable de la especificacion."
            ),
        )
