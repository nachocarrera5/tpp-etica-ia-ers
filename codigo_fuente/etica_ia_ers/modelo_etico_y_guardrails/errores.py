class ErrorRepositorioGuardrails(Exception):
    """Error base del repositorio de guardrails."""


class GuardrailDuplicadoError(ErrorRepositorioGuardrails):
    """Indica que ya existe la misma version de un guardrail."""
