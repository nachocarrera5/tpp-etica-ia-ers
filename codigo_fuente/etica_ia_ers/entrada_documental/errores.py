class ErrorCargaDocumento(Exception):
    """Error esperado durante la carga de una ERS."""


class FormatoNoSoportadoError(ErrorCargaDocumento):
    pass


class DocumentoVacioError(ErrorCargaDocumento):
    pass


class DocumentoIlegibleError(ErrorCargaDocumento):
    pass
