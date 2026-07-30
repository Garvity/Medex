import asyncio
from uuid import uuid4

from services.email_service import EmailDeliveryError
from services.reminder_worker import DeliveryClaim, deliver_claim
import services.reminder_worker as worker


def _claim() -> DeliveryClaim:
    return DeliveryClaim(
        delivery_id=uuid4(),
        reminder_id=uuid4(),
        user_id="firebase-user-id",
        recipient_email="patient@example.com",
        medicine="Aspirin",
        reminder_time="08:00 AM",
        timezone="Asia/Tokyo",
        frequency="daily",
        attempt_count=1,
    )


def test_delivery_marks_sent_with_a_stable_idempotency_key(monkeypatch) -> None:
    claim = _claim()
    captured: dict[str, str] = {}

    def fake_send_email(**kwargs):
        captured.update(kwargs)
        return "<smtp-message-id@medassist.local>"

    async def fake_mark_sent(sent_claim, message_id):
        captured["marked_delivery"] = str(sent_claim.delivery_id)
        captured["message_id"] = message_id

    monkeypatch.setattr(worker, "send_email", fake_send_email)
    monkeypatch.setattr(worker, "_mark_sent", fake_mark_sent)

    assert asyncio.run(deliver_claim(claim)) == "sent"
    assert captured["idempotency_key"] == str(claim.delivery_id)
    assert captured["marked_delivery"] == str(claim.delivery_id)
    assert "Asia/Tokyo" in captured["text"]


def test_delivery_marks_permanent_smtp_error_failed(monkeypatch) -> None:
    claim = _claim()

    def fake_send_email(**_kwargs):
        raise EmailDeliveryError("Invalid recipient", retryable=False)

    async def fake_mark_failure(_claim, error):
        assert error.retryable is False
        return "failed"

    monkeypatch.setattr(worker, "send_email", fake_send_email)
    monkeypatch.setattr(worker, "_mark_failure", fake_mark_failure)

    assert asyncio.run(deliver_claim(claim)) == "failed"
