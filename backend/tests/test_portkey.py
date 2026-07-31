import json

from agent.portkey import portkey_headers
from core.config import Settings


def test_portkey_headers_build_fallback_config() -> None:
    headers = portkey_headers(
        Settings(
            portkey_primary_virtual_key="@groq-primary",
            portkey_fallback_virtual_key="@groq-secondary",
        )
    )

    config = json.loads(headers["x-portkey-config"])
    assert config == {
        "strategy": {"mode": "fallback"},
        "targets": [
            {"virtual_key": "@groq-primary"},
            {"virtual_key": "@groq-secondary"},
        ],
    }


def test_portkey_headers_disable_fallback_when_target_is_missing() -> None:
    headers = portkey_headers(
        Settings(
            portkey_primary_virtual_key="@groq-primary",
            portkey_fallback_virtual_key=None,
        )
    )

    assert headers == {"x-portkey-provider": "@groq-primary"}
