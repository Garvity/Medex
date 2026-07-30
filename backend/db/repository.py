from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_profile(
    db: AsyncSession, user_id: str, name: str | None = None, email: str | None = None
) -> None:
    await db.execute(
        text(
            """insert into profiles (id, name, email) values (:id, :name, :email)
            on conflict (id) do update set
              name = coalesce(profiles.name, excluded.name),
              email = coalesce(excluded.email, profiles.email),
              updated_at = now()"""
        ),
        {"id": user_id, "name": name, "email": email},
    )
    await db.commit()


async def get_profile(db: AsyncSession, user_id: str):
    result = await db.execute(
        text("select id, name, phone, timezone from profiles where id = :user_id"), {"user_id": user_id}
    )
    return result.mappings().first()


async def update_profile(
    db: AsyncSession, user_id: str, name: str | None, phone: str | None, timezone: str | None
):
    result = await db.execute(
        text(
            """update profiles set name = coalesce(:name, name), phone = coalesce(:phone, phone),
            timezone = coalesce(:timezone, timezone), updated_at = now()
            where id = :user_id returning id, name, phone, timezone"""
        ),
        {"user_id": user_id, "name": name, "phone": phone, "timezone": timezone},
    )
    await db.commit()
    return result.mappings().one()


async def ensure_session(db: AsyncSession, user_id: str, session_id: UUID | None, initial_name: str) -> UUID:
    identifier = session_id or uuid4()
    result = await db.execute(
        text(
            """insert into chat_sessions (id, user_id, name) values (:id, :user_id, :name)
            on conflict (id) do update set updated_at = now()
            where chat_sessions.user_id = :user_id
            returning id"""
        ),
        {"id": identifier, "user_id": user_id, "name": initial_name[:120] or "New consultation"},
    )
    await db.commit()
    row = result.mappings().first()
    if not row:
        raise PermissionError("The requested session does not belong to the authenticated user.")
    return UUID(str(row["id"]))


async def add_message(
    db: AsyncSession, *, session_id: UUID, user_id: str, query: str, response: str, role: str, sources: list[dict]
):
    result = await db.execute(
        text(
            """insert into chat_messages (session_id, user_id, query, response, role, sources)
            values (:session_id, :user_id, :query, :response, :role, cast(:sources as jsonb))
            returning id, session_id, query, response, role, sources, created_at"""
        ),
        {
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "response": response,
            "role": role,
            "sources": __import__("json").dumps(sources),
        },
    )
    await db.execute(text("update chat_sessions set updated_at = now() where id = :id"), {"id": session_id})
    await db.commit()
    return result.mappings().one()


async def list_sessions(db: AsyncSession, user_id: str):
    result = await db.execute(
        text("select id, name, created_at, updated_at from chat_sessions where user_id = :user_id order by updated_at desc"),
        {"user_id": user_id},
    )
    return result.mappings().all()


async def list_messages(db: AsyncSession, user_id: str, session_id: UUID):
    result = await db.execute(
        text(
            """select id, session_id, query, response, role, sources, created_at from chat_messages
            where user_id = :user_id and session_id = :session_id order by created_at asc"""
        ),
        {"user_id": user_id, "session_id": session_id},
    )
    return result.mappings().all()


async def rename_session(db: AsyncSession, user_id: str, session_id: UUID, name: str):
    result = await db.execute(
        text(
            """update chat_sessions set name = :name, updated_at = now()
            where id = :session_id and user_id = :user_id returning id, name, created_at, updated_at"""
        ),
        {"user_id": user_id, "session_id": session_id, "name": name},
    )
    await db.commit()
    return result.mappings().first()


async def delete_session(db: AsyncSession, user_id: str, session_id: UUID) -> bool:
    result = await db.execute(
        text("delete from chat_sessions where id = :session_id and user_id = :user_id"),
        {"user_id": user_id, "session_id": session_id},
    )
    await db.commit()
    return bool(result.rowcount)


async def list_reminders(db: AsyncSession, user_id: str):
    result = await db.execute(
        text(
            """select id, medicine, reminder_time, timezone, frequency, notification_pref, status, last_triggered_at,
            next_occurrence_at
            from reminders where user_id = :user_id order by created_at desc"""
        ),
        {"user_id": user_id},
    )
    return result.mappings().all()


async def create_reminder(db: AsyncSession, user_id: str, payload: dict):
    result = await db.execute(
        text(
            """insert into reminders
            (user_id, medicine, reminder_time, timezone, frequency, notification_pref, next_occurrence_at)
            values (:user_id, :medicine, :reminder_time, :timezone, :frequency, :notification_pref, :next_occurrence_at)
            returning id, medicine, reminder_time, timezone, frequency, notification_pref, status, last_triggered_at,
            next_occurrence_at"""
        ),
        {"user_id": user_id, **payload},
    )
    await db.commit()
    return result.mappings().one()


async def update_reminder(db: AsyncSession, user_id: str, reminder_id: UUID, payload: dict):
    # Unsent occurrences based on the old schedule are no longer valid after an edit.
    # A delivery already being sent remains intact so a worker is never racing a cancellation.
    await db.execute(
        text(
            """delete from reminder_deliveries
            where reminder_id = :id and user_id = :user_id
              and status in ('pending', 'retrying') and scheduled_for >= now()"""
        ),
        {"id": reminder_id, "user_id": user_id},
    )
    result = await db.execute(
        text(
            """update reminders set medicine = :medicine, reminder_time = :reminder_time, timezone = :timezone,
            frequency = :frequency, notification_pref = :notification_pref, status = :status,
            next_occurrence_at = :next_occurrence_at, updated_at = now()
            where id = :id and user_id = :user_id
            returning id, medicine, reminder_time, timezone, frequency, notification_pref, status, last_triggered_at,
            next_occurrence_at"""
        ),
        {"id": reminder_id, "user_id": user_id, **payload},
    )
    await db.commit()
    return result.mappings().first()


async def delete_reminder(db: AsyncSession, user_id: str, reminder_id: UUID) -> bool:
    result = await db.execute(
        text("delete from reminders where id = :id and user_id = :user_id"),
        {"id": reminder_id, "user_id": user_id},
    )
    await db.commit()
    return bool(result.rowcount)


async def mark_reminder_triggered(db: AsyncSession, user_id: str, reminder_id: UUID):
    result = await db.execute(
        text(
            """update reminders set last_triggered_at = now(), updated_at = now()
            where id = :id and user_id = :user_id
            returning id, medicine, reminder_time, timezone, frequency, notification_pref, status, last_triggered_at,
            next_occurrence_at"""
        ),
        {"id": reminder_id, "user_id": user_id},
    )
    await db.commit()
    return result.mappings().first()
