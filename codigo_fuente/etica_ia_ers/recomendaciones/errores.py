class ErrorGeneracionRecomendaciones(Exception):
    """Error base de la generacion de alertas y recomendaciones."""


class ResultadosIncompatiblesError(ErrorGeneracionRecomendaciones):
    """La evaluacion y la cobertura no conservan la misma trazabilidad."""
