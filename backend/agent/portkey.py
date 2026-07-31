"""Shared Portkey gateway headers for model and guardrail requests."""

from core.config import Settings, get_settings


def portkey_headers(settings: Settings | None = None) -> dict[str, str]:
    """Reference the fallback configuration saved in Portkey.

    The workspace blocks inline configurations, so the application must send
    the saved ``pc-...`` slug rather than serializing fallback targets itself.
    """
    active_settings = settings or get_settings()
    config_id = (active_settings.portkey_config_id or "").strip()

    if not config_id:
        raise RuntimeError("PORTKEY_CONFIG_ID must be configured before model requests can run.")
    if not config_id.startswith("pc-"):
        raise ValueError("PORTKEY_CONFIG_ID must be a saved Portkey config slug beginning with 'pc-'.")

    return {"x-portkey-config": config_id}
