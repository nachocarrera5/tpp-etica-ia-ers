class ErrorEvaluacionEtica(Exception):
    """Error base de la evaluacion etica documental."""


class EvidenciaInvalidaError(ErrorEvaluacionEtica):
    """Indica que una evidencia no puede trazarse al resultado NLP."""


class EvaluacionGuardrailInvalidaError(ErrorEvaluacionEtica):
    """Indica que la salida preliminar de un guardrail es inconsistente."""
