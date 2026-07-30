import asyncio

import pytest
from fastapi import HTTPException

import api


def test_external_worker_trigger_requires_configured_secret(monkeypatch) -> None:
    monkeypatch.setattr(api.settings, "reminder_worker_trigger_token", None)
    with pytest.raises(HTTPException) as error:
        asyncio.run(api.run_reminder_worker(x_reminder_worker_token="anything"))
    assert error.value.status_code == 503


def test_external_worker_trigger_rejects_wrong_secret(monkeypatch) -> None:
    monkeypatch.setattr(api.settings, "reminder_worker_trigger_token", "expected-secret")
    with pytest.raises(HTTPException) as error:
        asyncio.run(api.run_reminder_worker(x_reminder_worker_token="wrong-secret"))
    assert error.value.status_code == 401


def test_external_worker_trigger_runs_the_existing_worker(monkeypatch) -> None:
    async def fake_run_once():
        return {"claimed": 1, "sent": 1, "retrying": 0, "failed": 0}

    monkeypatch.setattr(api.settings, "reminder_worker_trigger_token", "expected-secret")
    monkeypatch.setattr(api, "run_reminder_worker_once", fake_run_once)
    assert asyncio.run(api.run_reminder_worker(x_reminder_worker_token="expected-secret")) == {
        "claimed": 1,
        "sent": 1,
        "retrying": 0,
        "failed": 0,
    }
