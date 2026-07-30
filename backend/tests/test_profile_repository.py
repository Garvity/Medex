import asyncio

from db import repository
from db.models import Profile


class RecordingSession:
    def __init__(self) -> None:
        self.statement = ""
        self.params: dict = {}
        self.committed = False

    async def execute(self, statement, params):
        self.statement = str(statement)
        self.params = params

    async def commit(self):
        self.committed = True


def test_ensure_profile_upserts_firebase_email() -> None:
    session = RecordingSession()
    asyncio.run(repository.ensure_profile(session, "firebase-uid", "Patient", "patient@example.com"))

    assert "insert into profiles (id, name, email)" in session.statement
    assert "email = coalesce(excluded.email, profiles.email)" in session.statement
    assert session.params == {"id": "firebase-uid", "name": "Patient", "email": "patient@example.com"}
    assert session.committed is True


def test_profile_model_contains_nullable_firebase_email() -> None:
    email = Profile.__table__.c.email
    assert email.nullable is True
    assert str(email.type) in {"TEXT", "VARCHAR"}
