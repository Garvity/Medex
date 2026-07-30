"""Standalone worker that delivers due medication-reminder emails through Gmail SMTP.

Run this module independently of FastAPI, usually once per minute:
    python -m services.reminder_worker
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text

from core.config import get_settings
from db.database import SessionLocal
from services.email_service import EmailDeliveryError, send_email
from services.email_templates import medication_reminder_email
from services.reminder_service import next_occurrence, retry_at

logger = logging.getLogger("medassist.reminder_worker")


@dataclass(frozen=True)
class DeliveryClaim:
    delivery_id: UUID
    reminder_id: UUID
    user_id: str
    recipient_email: str
    medicine: str
    reminder_time: str
    timezone: str
    frequency: str
    attempt_count: int


def _masked_email(email: str) -> str:
    local, separator, domain = email.partition("@")
    if not separator:
        return "***"
    return f"{local[:1]}***@{domain}"


async def _requeue_stale_claims(session: Any) -> None:
    settings = get_settings()
    params = {"timeout_minutes": settings.reminder_claim_timeout_minutes, "max_attempts": settings.reminder_max_attempts}
    await session.execute(
        text(
            """update reminder_deliveries
            set status = 'retrying', locked_at = null, next_retry_at = now(),
                last_error = coalesce(last_error, 'Worker claim timed out.'), updated_at = now()
            where status = 'sending'
              and locked_at < now() - (:timeout_minutes * interval '1 minute')
              and attempt_count < :max_attempts"""
        ),
        params,
    )
    await session.execute(
        text(
            """update reminder_deliveries
            set status = 'failed', locked_at = null,
                last_error = coalesce(last_error, 'Maximum delivery attempts exceeded after worker claim timeout.'),
                updated_at = now()
            where status = 'sending'
              and locked_at < now() - (:timeout_minutes * interval '1 minute')
              and attempt_count >= :max_attempts"""
        ),
        params,
    )


async def _claim_due_reminders(session: Any, limit: int) -> list[DeliveryClaim]:
    result = await session.execute(
        text(
            """select r.id as reminder_id, r.user_id, r.medicine, r.reminder_time, r.frequency,
                      r.timezone, r.next_occurrence_at, p.email as recipient_email
            from reminders r
            join profiles p on p.id = r.user_id
            where r.status = 'active'
              and r.next_occurrence_at <= now()
              and p.email is not null and p.email <> ''
              and r.notification_pref ~ '(^|,)email(,|$)'
            order by r.next_occurrence_at, r.id
            limit :limit
            for update of r skip locked"""
        ),
        {"limit": limit},
    )
    claims: list[DeliveryClaim] = []
    for row in result.mappings():
        scheduled_for: datetime = row["next_occurrence_at"]
        insert = await session.execute(
            text(
                """insert into reminder_deliveries
                (reminder_id, user_id, scheduled_for, recipient_email, status, attempt_count, locked_at)
                values (:reminder_id, :user_id, :scheduled_for, :recipient_email, 'sending', 1, now())
                on conflict (reminder_id, scheduled_for) do nothing
                returning id, attempt_count"""
            ),
            {
                "reminder_id": row["reminder_id"],
                "user_id": row["user_id"],
                "scheduled_for": scheduled_for,
                "recipient_email": row["recipient_email"],
            },
        )
        delivery = insert.mappings().first()
        if not delivery:
            # A unique occurrence exists already. Advance the schedule only if another
            # worker has not done so, avoiding a permanently due reminder on recovery.
            await session.execute(
                text(
                    """update reminders set next_occurrence_at = :following, updated_at = now(),
                    status = case when frequency = 'once' then 'completed' else status end
                    where id = :id and next_occurrence_at = :scheduled_for"""
                ),
                {
                    "id": row["reminder_id"],
                    "scheduled_for": scheduled_for,
                    "following": next_occurrence(scheduled_for, row["frequency"], row["timezone"]),
                },
            )
            continue
        following = next_occurrence(scheduled_for, row["frequency"], row["timezone"])
        await session.execute(
            text(
                """update reminders set next_occurrence_at = :following, updated_at = now(),
                status = case when frequency = 'once' then 'completed' else status end
                where id = :id"""
            ),
            {"id": row["reminder_id"], "following": following},
        )
        claims.append(
            DeliveryClaim(
                delivery_id=UUID(str(delivery["id"])),
                reminder_id=UUID(str(row["reminder_id"])),
                user_id=row["user_id"],
                recipient_email=row["recipient_email"],
                medicine=row["medicine"],
                reminder_time=row["reminder_time"],
                timezone=row["timezone"],
                frequency=row["frequency"],
                attempt_count=delivery["attempt_count"],
            )
        )
    return claims


async def _claim_retries(session: Any, limit: int) -> list[DeliveryClaim]:
    if limit <= 0:
        return []
    result = await session.execute(
        text(
            """select d.id as delivery_id, d.reminder_id, d.user_id, d.recipient_email, d.attempt_count,
                      r.medicine, r.reminder_time, r.timezone, r.frequency
            from reminder_deliveries d
            join reminders r on r.id = d.reminder_id
            where d.status in ('pending', 'retrying')
              and coalesce(d.next_retry_at, d.created_at) <= now()
            order by coalesce(d.next_retry_at, d.created_at), d.id
            limit :limit
            for update of d skip locked"""
        ),
        {"limit": limit},
    )
    claims: list[DeliveryClaim] = []
    for row in result.mappings():
        claimed = await session.execute(
            text(
                """update reminder_deliveries set status = 'sending', attempt_count = attempt_count + 1,
                locked_at = now(), updated_at = now()
                where id = :id and status in ('pending', 'retrying')
                returning attempt_count"""
            ),
            {"id": row["delivery_id"]},
        )
        attempt_count = claimed.scalar_one_or_none()
        if attempt_count is None:
            continue
        claims.append(
            DeliveryClaim(
                delivery_id=UUID(str(row["delivery_id"])),
                reminder_id=UUID(str(row["reminder_id"])),
                user_id=row["user_id"],
                recipient_email=row["recipient_email"],
                medicine=row["medicine"],
                reminder_time=row["reminder_time"],
                timezone=row["timezone"],
                frequency=row["frequency"],
                attempt_count=attempt_count,
            )
        )
    return claims


async def claim_deliveries(batch_size: int) -> list[DeliveryClaim]:
    """Atomically reserve due occurrences and retries before any external I/O."""
    async with SessionLocal() as session:
        async with session.begin():
            await _requeue_stale_claims(session)
            claims = await _claim_due_reminders(session, batch_size)
            claims.extend(await _claim_retries(session, batch_size - len(claims)))
        return claims


async def _mark_sent(claim: DeliveryClaim, provider_message_id: str) -> None:
    async with SessionLocal() as session:
        async with session.begin():
            await session.execute(
                text(
                    """update reminder_deliveries set status = 'sent', provider_message_id = :message_id,
                    sent_at = now(), locked_at = null, last_error = null, updated_at = now()
                    where id = :id and status = 'sending'"""
                ),
                {"id": claim.delivery_id, "message_id": provider_message_id or None},
            )
            await session.execute(
                text("update reminders set last_triggered_at = now(), updated_at = now() where id = :id"),
                {"id": claim.reminder_id},
            )


async def _mark_failure(claim: DeliveryClaim, error: EmailDeliveryError) -> str:
    settings = get_settings()
    should_retry = error.retryable and claim.attempt_count < settings.reminder_max_attempts
    new_status = "retrying" if should_retry else "failed"
    async with SessionLocal() as session:
        async with session.begin():
            await session.execute(
                text(
                    """update reminder_deliveries set status = :status, next_retry_at = :next_retry_at,
                    locked_at = null, last_error = :last_error, updated_at = now()
                    where id = :id and status = 'sending'"""
                ),
                {
                    "id": claim.delivery_id,
                    "status": new_status,
                    "next_retry_at": retry_at(claim.attempt_count) if should_retry else None,
                    "last_error": str(error.message)[:1000],
                },
            )
    return new_status


async def deliver_claim(claim: DeliveryClaim) -> str:
    subject, text_body, html = medication_reminder_email(
        medicine=claim.medicine,
        scheduled_time=f"{claim.reminder_time} ({claim.timezone})",
        frequency=claim.frequency,
    )
    try:
        message_id = await asyncio.to_thread(
            send_email,
            recipient=claim.recipient_email,
            subject=subject,
            text=text_body,
            html=html,
            idempotency_key=str(claim.delivery_id),
        )
    except EmailDeliveryError as exc:
        delivery_status = await _mark_failure(claim, exc)
        logger.warning(
            "reminder_delivery status=%s reminder_id=%s user_id=%s recipient=%s error=%s",
            delivery_status,
            claim.reminder_id,
            claim.user_id,
            _masked_email(claim.recipient_email),
            str(exc.message)[:300],
        )
        return delivery_status
    except Exception as exc:  # Treat unexpected transport/runtime faults as transient.
        delivery_status = await _mark_failure(claim, EmailDeliveryError(str(exc), retryable=True))
        logger.exception(
            "reminder_delivery status=%s reminder_id=%s user_id=%s recipient=%s",
            delivery_status,
            claim.reminder_id,
            claim.user_id,
            _masked_email(claim.recipient_email),
        )
        return delivery_status
    await _mark_sent(claim, message_id)
    logger.info(
        "reminder_delivery status=sent reminder_id=%s user_id=%s recipient=%s provider_message_id=%s",
        claim.reminder_id,
        claim.user_id,
        _masked_email(claim.recipient_email),
        message_id or "none",
    )
    return "sent"


async def run_once(batch_size: int | None = None) -> dict[str, int]:
    size = batch_size or get_settings().reminder_worker_batch_size
    if size < 1:
        raise ValueError("batch_size must be at least 1")
    claims = await claim_deliveries(size)
    outcomes = await asyncio.gather(*(deliver_claim(claim) for claim in claims))
    summary = {"claimed": len(claims), "sent": 0, "retrying": 0, "failed": 0}
    for outcome in outcomes:
        summary[outcome] = summary.get(outcome, 0) + 1
    logger.info("reminder_worker_summary %s", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Deliver due MedAssist medication reminders through Gmail SMTP.")
    parser.add_argument("--batch-size", type=int, default=None, help="Maximum deliveries to claim in one run.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_once(args.batch_size))


if __name__ == "__main__":
    main()
