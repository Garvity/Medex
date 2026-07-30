# MedAssist architecture

## Runtime topology

```text
React + Firebase Auth
        │ Firebase ID token
        ▼
FastAPI API
        ├── Firebase Admin token verification
        ├── PostgreSQL application repository
        └── LangGraph medical workflow
              ├── NeMo Guardrails + deterministic emergency checks
              ├── Qdrant hybrid retrieval (Jina dense + BM25 sparse)
              ├── FlashRank reranking
              ├── Portkey gateway
              └── Groq: llama-3.3-70b-versatile

Standalone reminder worker
        ├── PostgreSQL occurrence and delivery state
        └── Gmail SMTP (STARTTLS)
```

Docker Compose starts only the two local stateful services: PostgreSQL and Qdrant. Firebase
Cloud, Jina, Portkey, Groq, and Logfire are external managed services configured through
environment variables.

The React client in `frontend/` is the maintained user interface.

## Local startup

1. Copy `.env.example` to `.env` and `backend/.env.example` to `backend/.env`.
2. Add Firebase Cloud, Jina, Portkey, Groq, and optionally Logfire credentials to `backend/.env`.
3. Copy `frontend/.env.example` to `frontend/.env` and add the Firebase Web App configuration.
4. Start the databases with `docker compose up -d`.
5. Install backend packages: `cd backend && python -m pip install -r requirements.txt`.
6. Apply database migrations: `alembic upgrade head`.
7. Index the existing normalized medical corpus once:

   ```bash
   cd backend
   python -m retrieval.ingest
   ```

8. Start the API: `uvicorn api:app --reload`.
9. Start the client: `cd frontend && npm install && npm run dev`.

## Identity and data ownership

Firebase Cloud Auth owns authentication. The frontend retrieves a Firebase ID token for every
API request; FastAPI verifies it with Firebase Admin before reading or writing PostgreSQL.
PostgreSQL owns profiles, sessions, messages, reminders, and evaluation run records. Qdrant
contains only searchable medical knowledge chunks and their metadata.

## Medication email reminders

Email reminders are not scheduled from FastAPI or the browser. Before enabling the worker on an
existing database, apply `alembic upgrade head` from `backend/`. The Alembic migration adds the
Firebase email and timezone fields required by the current profile contract. The reminder
delivery migrations add timezone-aware schedules and idempotent delivery records.

Run the standalone worker every minute through cron, Docker, or a managed scheduler:

```bash
cd backend
python -m services.reminder_worker
```

The worker claims rows with `FOR UPDATE SKIP LOCKED`, records each unique `(reminder_id,
scheduled_for)` occurrence, retries network/429/5xx failures with backoff, and logs delivery
status plus the SMTP Message-ID. It must have Gmail SMTP credentials, including a Google App
Password—not an account password—configured through `SMTP_*` variables. The UI's Email checkbox
queues server-side delivery and never sends mail from the browser.

For EasyCron over a Cloudflare Tunnel, set a long random `REMINDER_WORKER_TRIGGER_TOKEN` in
`backend/.env`, restart the API, then schedule an HTTP `POST` every minute to
`https://<your-tunnel-host>/internal/reminders/run`. Configure the request header
`X-Reminder-Worker-Token` with the same secret. Do not place the token in the URL.

## Evaluation

`backend/tests/golden_queries.json` is the starting retrieval regression suite. Run
`python backend/tests/evaluation.py` after indexing. It reports Top-1 accuracy, Recall@k, MRR,
and nDCG@k. Add representative, reviewed medical queries to this file before deploying dataset,
chunking, embedding, or reranking changes.
