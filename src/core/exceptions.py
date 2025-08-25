"""
Excepciones personalizadas del proyecto.
"""


class SayenException(Exception):
    """Excepción base del proyecto."""
    pass


class AuthenticationError(SayenException):
    """Error de autenticación."""
    pass


class ScrapingError(SayenException):
    """Error durante el scraping."""
    pass


class DataValidationError(SayenException):
    """Error de validación de datos."""
    pass


class ExcelProcessingError(SayenException):
    """Error procesando archivos Excel."""
    pass