import pytest

from agent.portkey import portkey_headers
from core.config import Settings


def test_portkey_headers_reference_saved_config() -> None:
    headers = portkey_headers(Settings(portkey_config_id="pc-fallback-config"))

    assert headers == {"x-portkey-config": "pc-fallback-config"}


def test_portkey_headers_require_saved_config() -> None:
    with pytest.raises(RuntimeError, match="PORTKEY_CONFIG_ID"):
        portkey_headers(Settings(portkey_config_id=None))


def test_portkey_headers_reject_non_config_identifier() -> None:
    with pytest.raises(ValueError, match="beginning with 'pc-'"):
        portkey_headers(Settings(portkey_config_id="@rag"))
