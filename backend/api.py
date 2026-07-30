from contextlib import asynccontextmanager
import asyncio
import logging
import secrets
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent.workflow import get_retriever, run_medical_workflow
from core.auth import get_current_user
from core.config import get_settings
from core.observability import configure_observability
from db.database import get_db
from db import repository
from services.reminder_service import first_occurrence, normalize_notification_preferences, validate_timezone
from services.reminder_worker import run_once as run_reminder_worker_once
from schemas import (
    ChatMessageResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    QueryRequest,
    QueryResponse,
    ReminderCreateRequest,
    ReminderResponse,
    ReminderUpdateRequest,
    SessionResponse,
    SessionUpdateRequest,
)
from retrieval.qdrant_retriever import KnowledgeBaseNotReady


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


settings = get_settings()
app = FastAPI(title="MedAssist API", version="3.0.0", lifespan=lifespan)
configure_observability(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_, exc: RequestValidationError):
    """Make client request-contract failures actionable while retaining FastAPI's 422 response."""
    errors = exc.errors()
    logging.getLogger("medassist.validation").warning("Request validation failed: %s", errors)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": errors})


def user_name(user: dict) -> str | None:
    return user.get("name") or user.get("display_name") or user.get("email")


async def ensure_user(db: AsyncSession, user: dict) -> str:
    user_id = str(user["uid"])
    await repository.ensure_profile(db, user_id, user_name(user), user.get("email"))
    return user_id


@app.get("/health")
async def health_check():
    try:
        knowledge_base = await asyncio.to_thread(get_retriever().knowledge_base_status)
    except Exception as exc:
        knowledge_base = {"collection_exists": False, "points_count": 0, "error": str(exc)}
    return {"status": "ok", "version": app.version, "knowledge_base": knowledge_base}


@app.post("/internal/reminders/run")
async def run_reminder_worker(
    x_reminder_worker_token: str | None = Header(default=None),
):
    """Secure external trigger for EasyCron or another managed scheduler.

    This endpoint does not schedule work inside FastAPI; it invokes the same independent
    worker routine that is available through ``python -m services.reminder_worker``.
    """
    configured_token = settings.reminder_worker_trigger_token
    if not configured_token:
        logging.getLogger("medassist.reminder_worker").error("Reminder worker trigger token is not configured.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reminder worker trigger is not configured.")
    if not x_reminder_worker_token or not secrets.compare_digest(x_reminder_worker_token, configured_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reminder worker trigger token.")
    try:
        return await run_reminder_worker_once()
    except Exception as exc:
        logging.getLogger("medassist.reminder_worker").exception("Externally triggered reminder worker failed.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Reminder worker execution failed.") from exc


@app.post("/ask", response_model=QueryResponse)
async def ask(
    request: QueryRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    try:
        session_id = await repository.ensure_session(db, user_id, request.session_id, request.query)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    try:
        result = await run_medical_workflow(request.query, request.role, request.history)
    except KnowledgeBaseNotReady as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    await repository.add_message(
        db,
        session_id=session_id,
        user_id=user_id,
        query=request.query,
        response=result["answer"],
        role=request.role,
        sources=result["sources"],
    )
    return QueryResponse(
        response=result["answer"],
        session_id=session_id,
        sources=result["sources"],
        guardrail_action=result["guardrail_action"],
    )


@app.get("/profile", response_model=ProfileResponse)
async def get_profile(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = await ensure_user(db, user)
    profile = await repository.get_profile(db, user_id)
    return ProfileResponse(**dict(profile))


@app.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    try:
        timezone = validate_timezone(request.timezone) if request.timezone else None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    profile = await repository.update_profile(db, user_id, request.name, request.phone, timezone)
    return ProfileResponse(**dict(profile))


@app.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = await ensure_user(db, user)
    return [SessionResponse(**dict(row)) for row in await repository.list_sessions(db, user_id)]


@app.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def list_messages(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    return [ChatMessageResponse(**dict(row)) for row in await repository.list_messages(db, user_id, session_id)]


@app.put("/sessions/{session_id}", response_model=SessionResponse)
async def rename_session(
    session_id: UUID,
    request: SessionUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    session = await repository.rename_session(db, user_id, session_id, request.name)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return SessionResponse(**dict(session))


@app.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    if not await repository.delete_session(db, user_id, session_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")


@app.get("/reminders", response_model=list[ReminderResponse])
async def list_reminders(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = await ensure_user(db, user)
    return [ReminderResponse(**dict(row)) for row in await repository.list_reminders(db, user_id)]


@app.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    request: ReminderCreateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    payload = request.model_dump()
    try:
        payload["timezone"] = validate_timezone(payload["timezone"])
        payload["notification_pref"] = normalize_notification_preferences(payload["notification_pref"])
        payload["next_occurrence_at"] = first_occurrence(payload["reminder_time"], payload["timezone"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    reminder = await repository.create_reminder(db, user_id, payload)
    return ReminderResponse(**dict(reminder))


@app.put("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    request: ReminderUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    payload = request.model_dump()
    try:
        payload["timezone"] = validate_timezone(payload["timezone"])
        payload["notification_pref"] = normalize_notification_preferences(payload["notification_pref"])
        payload["next_occurrence_at"] = (
            first_occurrence(payload["reminder_time"], payload["timezone"])
            if payload["status"] == "active"
            else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    reminder = await repository.update_reminder(db, user_id, reminder_id, payload)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
    return ReminderResponse(**dict(reminder))


@app.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    if not await repository.delete_reminder(db, user_id, reminder_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")


@app.post("/reminders/{reminder_id}/trigger", response_model=ReminderResponse)
async def mark_reminder_triggered(
    reminder_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await ensure_user(db, user)
    reminder = await repository.mark_reminder_triggered(db, user_id, reminder_id)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
    return ReminderResponse(**dict(reminder))
