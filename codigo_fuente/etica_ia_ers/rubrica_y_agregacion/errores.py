class ErrorRubricaYAgregacion(Exception):
    """Error base del calculo de cobertura documental."""


class ResultadoEvaluacionInvalidoError(ErrorRubricaYAgregacion):
    """El resultado etico no conserva la trazabilidad requerida."""
