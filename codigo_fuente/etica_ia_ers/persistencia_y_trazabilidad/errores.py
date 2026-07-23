class ErrorAlmacenamiento(Exception):
    """Error esperado durante el almacenamiento o la recuperacion de una ERS."""


class DocumentoNoEncontradoError(ErrorAlmacenamiento):
    pass


class DocumentoYaRegistradoError(ErrorAlmacenamiento):
    pass


class TextoNormalizadoInvalidoError(ErrorAlmacenamiento):
    """El texto normalizado no corresponde al documento almacenado."""


class AlmacenamientoCorruptoError(ErrorAlmacenamiento):
    """Lo almacenado existe pero no puede interpretarse."""
