from __future__ import annotations

from typing import Iterable, Protocol, Tuple, runtime_checkable

from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    DefinicionGuardrail,
    EvaluacionPreliminarGuardrail,
)

from .errores import GuardrailDuplicadoError


@runtime_checkable
class GuardrailEvaluable(Protocol):
    @property
    def definicion(self) -> DefinicionGuardrail:
        ...

    def decidir_aplicabilidad(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> DecisionAplicabilidad:
        ...

    def evaluar(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> EvaluacionPreliminarGuardrail:
        ...


@runtime_checkable
class RepositorioGuardrails(Protocol):
    def listar(self) -> Tuple[GuardrailEvaluable, ...]:
        ...


class RepositorioGuardrailsEnMemoria:
    def __init__(
        self,
        guardrails: Iterable[GuardrailEvaluable] = (),
    ) -> None:
        elementos = tuple(guardrails)
        claves = set()

        for guardrail in elementos:
            clave = guardrail.definicion.clave_versionada
            if clave in claves:
                codigo, version = clave
                raise GuardrailDuplicadoError(
                    f"El guardrail {codigo} version {version} esta duplicado."
                )
            claves.add(clave)

        self._guardrails = elementos

    def listar(self) -> Tuple[GuardrailEvaluable, ...]:
        return self._guardrails
