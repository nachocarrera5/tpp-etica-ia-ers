class ErrorExportacion(Exception):
    """Error base de la exportacion de reportes de cobertura documental."""


class FormatoExportacionNoSoportadoError(ErrorExportacion):
    """El formato pedido no esta contemplado por el exportador."""


class ReporteInvalidoError(ErrorExportacion):
    """El reporte recibido no respeta el formato de resultados esperado."""


class ErrorEscrituraReporte(ErrorExportacion):
    """El reporte no pudo escribirse en el directorio de salida."""
