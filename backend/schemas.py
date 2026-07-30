from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=6000)
    role: str = Field(default="user", pattern="^(user|doctor)$")
    session_id: UUID | None = None
    history: list[dict[str, str]] | None = None


class QueryResponse(BaseModel):
    response: str
    session_id: UUID
    sources: list[dict]
    guardrail_action: str = "allow"


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)


class ProfileResponse(BaseModel):
    id: str
    name: str | None = None
    phone: str | None = None
    timezone: str = "Asia/Kolkata"


class ReminderCreateRequest(BaseModel):
    medicine: str = Field(min_length=1, max_length=160)
    reminder_time: str = Field(min_length=1, max_length=40)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=64)
    frequency: str = Field(default="once", pattern="^(once|daily|weekly|every_8_hours)$")
    notification_pref: str = Field(default="in_app", max_length=100)


class ReminderUpdateRequest(ReminderCreateRequest):
    status: str = Field(default="active", pattern="^(active|completed)$")


class ReminderResponse(BaseModel):
    id: UUID
    medicine: str
    reminder_time: str
    frequency: str
    notification_pref: str
    status: str
    last_triggered_at: datetime | None = None
    next_occurrence_at: datetime | None = None


class SessionUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class SessionResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    query: str
    response: str
    role: str
    sources: list[dict]
    created_at: datetime
