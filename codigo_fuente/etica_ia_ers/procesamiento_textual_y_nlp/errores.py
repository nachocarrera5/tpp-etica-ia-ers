class ErrorNormalizacion(Exception):
    """Error esperado durante la normalización de texto de una ERS."""


class TextoVacioError(ErrorNormalizacion):
    pass


class PasoDesconocidoError(ErrorNormalizacion):
    pass


class ErrorEnPasoDeNormalizacion(ErrorNormalizacion):
    """Un paso individual de normalización falló inesperadamente."""

    def __init__(self, nombre_paso: str, causa: Exception) -> None:
        self.nombre_paso = nombre_paso
        self.causa = causa
        super().__init__(
            f"Error en el paso '{nombre_paso}': {causa}"
        )
