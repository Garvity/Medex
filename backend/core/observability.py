import logging

from core.config import get_settings


def configure_observability(app=None) -> None:
    """Configure Logfire when a token is supplied; local development remains dependency-safe."""
    settings = get_settings()
    try:
        import logfire

        logfire.configure(
            token=settings.logfire_token,
            service_name=settings.logfire_service_name,
            send_to_logfire="if-token-present",
        )
        if app is not None:
            logfire.instrument_fastapi(app)
        logfire.instrument_httpx()
    except Exception as exc:  # Observability must never prevent API startup.
        logging.getLogger(__name__).warning("Logfire setup skipped: %s", exc)
