"""Shared Portkey gateway headers for model and guardrail requests."""

import json

from core.config import Settings, get_settings


def portkey_headers(settings: Settings | None = None) -> dict[str, str]:
    """Return headers for a Portkey fallback route.

    Portkey virtual keys identify the provider credentials stored in Portkey.
    Supplying both targets in a fallback config is what enables failover; a
    second ``x-portkey-provider-api-key`` header cannot represent a fallback.
    """
    active_settings = settings or get_settings()
    primary = active_settings.portkey_primary_virtual_key.strip()
    fallback = (active_settings.portkey_fallback_virtual_key or "").strip()

    if not primary:
        raise ValueError("PORTKEY_PRIMARY_VIRTUAL_KEY must not be empty.")

    if not fallback or fallback == primary:
        return {"x-portkey-provider": primary}

    config = {
        "strategy": {"mode": "fallback"},
        "targets": [
            {"virtual_key": primary},
            {"virtual_key": fallback},
        ],
    }
    return {"x-portkey-config": json.dumps(config, separators=(",", ":"))}
