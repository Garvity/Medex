"""Gmail SMTP transport for reminder emails.

The reminder worker owns scheduling, retrying, and delivery idempotency. This module only
constructs and sends one MIME message through SMTP.
"""

from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid
import smtplib
import socket
import ssl

from core.config import get_settings


@dataclass
class EmailDeliveryError(RuntimeError):
    message: str
    retryable: bool


def _smtp_error(exc: Exception) -> EmailDeliveryError:
    """Classify permanent SMTP rejections separately from transient failures."""
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return EmailDeliveryError("SMTP authentication failed. Check the Gmail App Password.", retryable=False)
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        codes = [code for code, _message in exc.recipients.values()]
        retryable = bool(codes) and any(code < 500 for code in codes)
        return EmailDeliveryError(f"SMTP rejected recipient ({', '.join(map(str, codes))}).", retryable=retryable)
    if isinstance(exc, smtplib.SMTPResponseException):
        return EmailDeliveryError(f"SMTP rejected delivery ({exc.smtp_code}).", retryable=exc.smtp_code < 500)
    if isinstance(exc, (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, socket.timeout, TimeoutError, OSError)):
        return EmailDeliveryError(f"SMTP network error: {exc}", retryable=True)
    if isinstance(exc, smtplib.SMTPException):
        return EmailDeliveryError(f"SMTP error: {exc}", retryable=True)
    return EmailDeliveryError(f"Unexpected SMTP error: {exc}", retryable=True)


def send_email(*, recipient: str, subject: str, text: str, html: str, idempotency_key: str | None = None) -> str:
    settings = get_settings()
    required = {
        "SMTP_USERNAME": settings.smtp_username,
        "SMTP_PASSWORD": settings.smtp_password,
        "SMTP_FROM": settings.smtp_from,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise EmailDeliveryError(f"Missing SMTP configuration: {', '.join(missing)}.", retryable=False)

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    if settings.smtp_reply_to:
        message["Reply-To"] = settings.smtp_reply_to
    # SMTP has no provider idempotency API. This stable Message-ID complements the
    # worker's unique occurrence record and makes retries traceable.
    message_id = f"<{idempotency_key}@medassist.local>" if idempotency_key else make_msgid()
    message["Message-ID"] = message_id
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
            client.ehlo()
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
            client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)
    except Exception as exc:
        raise _smtp_error(exc) from exc
    return message_id
