"""Configuración TLS basada en el almacén de certificados del sistema."""

_configured = False


def configure_system_certificate_store() -> None:
    """Integra las autoridades de confianza del sistema sin desactivar TLS."""

    global _configured
    if _configured:
        return

    try:
        import truststore
    except ImportError as exc:  # pragma: no cover - dependencia de ejecución
        raise RuntimeError("Instala la dependencia 'truststore'") from exc

    truststore.inject_into_ssl()
    _configured = True
