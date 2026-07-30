from types import SimpleNamespace

import pytest

import services.email_service as email_service
from services.email_service import EmailDeliveryError, send_email


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host: str, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.credentials: tuple[str, str] | None = None
        self.message = None
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def ehlo(self):
        return None

    def starttls(self, context):
        assert context is not None
        self.started_tls = True

    def login(self, username: str, password: str):
        self.credentials = (username, password)

    def send_message(self, message):
        self.message = message


def _settings(**overrides):
    values = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "sender@gmail.com",
        "smtp_password": "app-password",
        "smtp_from": "MedAssist AI <sender@gmail.com>",
        "smtp_reply_to": "sender@gmail.com",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_gmail_smtp_uses_starttls_and_returns_stable_message_id(monkeypatch) -> None:
    FakeSMTP.instances.clear()
    monkeypatch.setattr(email_service, "get_settings", lambda: _settings())
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    message_id = send_email(
        recipient="patient@example.com",
        subject="Reminder",
        text="Plain text",
        html="<p>HTML</p>",
        idempotency_key="delivery-123",
    )

    smtp = FakeSMTP.instances[0]
    assert smtp.host == "smtp.gmail.com"
    assert smtp.port == 587
    assert smtp.started_tls is True
    assert smtp.credentials == ("sender@gmail.com", "app-password")
    assert smtp.message["Message-ID"] == "<delivery-123@medassist.local>"
    assert message_id == "<delivery-123@medassist.local>"
    assert smtp.message.get_body(preferencelist=("html",)).get_content().strip() == "<p>HTML</p>"


def test_missing_gmail_credentials_is_a_permanent_error(monkeypatch) -> None:
    monkeypatch.setattr(email_service, "get_settings", lambda: _settings(smtp_password=None))
    with pytest.raises(EmailDeliveryError, match="SMTP_PASSWORD") as error:
        send_email(recipient="patient@example.com", subject="Reminder", text="Text", html="<p>Text</p>")
    assert error.value.retryable is False
