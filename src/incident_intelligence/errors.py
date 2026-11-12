"""Errores controlados del dominio."""


class IncidentIntelligenceError(Exception):
    """Error base del sistema."""


class LLMConfigurationError(IncidentIntelligenceError):
    """Configuración de proveedor o modelo inválida."""


class LLMProviderError(IncidentIntelligenceError):
    """Fallo de red, cuota o servicio del proveedor."""

