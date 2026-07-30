# MedAssist AI

> A full-stack, safety-oriented medical information assistant that combines grounded retrieval, agentic orchestration, authenticated patient context, and reliable medication reminders.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.14.2-DC244C?logo=qdrant&logoColor=white)](https://qdrant.tech/)

## Why MedAssist

MedAssist is built for medical information workflows where a fluent answer is not enough. It retrieves from a curated knowledge base, reranks evidence before generation, applies input/output safety controls, and clearly separates informational guidance from clinical diagnosis.

It also includes authenticated chat history and timezone-aware medication reminders with PostgreSQL-backed delivery state, external scheduling, retry handling, and Gmail SMTP delivery.

> MedAssist provides general medical information only. It is not a diagnostic, emergency, or prescribing system.

## Architecture

```mermaid
flowchart LR
    U["Patient or clinician"] --> UI["React + TypeScript UI"]
    UI -->|"Firebase ID token"| API["FastAPI API"]
    API --> AUTH["Firebase Auth"]
    API --> DB[("PostgreSQL")]
    API --> GRAPH["LangGraph workflow"]

    GRAPH --> GR["NeMo Guardrails"]
    GRAPH --> RET["Hybrid retrieval"]
    RET --> QD[("Qdrant")]
    RET --> JINA["Jina embeddings + BM25"]
    RET --> RERANK["FlashRank reranker"]
    GRAPH --> LLM["Portkey gateway → Groq LLM"]
    GRAPH --> OBS["Pydantic Logfire"]

    CRON["EasyCron"] -->|"authenticated POST"| TRIGGER["Reminder trigger endpoint"]
    TRIGGER --> WORKER["Standalone reminder worker"]
    WORKER --> DB
    WORKER --> SMTP["Gmail SMTP / STARTTLS"]
```

## Technical highlights

- Grounded medical answers from a curated corpus rather than unbounded model recall.
- Dense Jina retrieval plus BM25 sparse retrieval in Qdrant, followed by FlashRank reranking.
- LangGraph state machine for guard, retrieve, rerank, generate, and tool-routing stages.
- Firebase-verified API access; PostgreSQL owns profiles, conversations, reminders, and delivery audit history.
- Timezone-aware reminders with idempotent occurrences, row locking, retry backoff, and Gmail SMTP delivery.
- Evaluation utilities for Recall@k, MRR, nDCG, and Top-1 retrieval accuracy.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Web client | ![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white) ![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?logo=tailwindcss&logoColor=white) |
| API and validation | ![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?logo=fastapi&logoColor=white) ![Pydantic](https://img.shields.io/badge/Pydantic-2.11-ED9B17?logo=pydantic&logoColor=white) |
| Agentic RAG | ![LangChain](https://img.shields.io/badge/LangChain-0.3.27-1C3C3C?logo=langchain&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-0.6.5-1C3C3C?logo=langchain&logoColor=white) ![NeMo Guardrails](https://img.shields.io/badge/NeMo_Guardrails-0.23.0-76B900?logo=nvidia&logoColor=white) |
| Retrieval | ![Qdrant](https://img.shields.io/badge/Qdrant-1.14.2-DC244C?logo=qdrant&logoColor=white) ![Jina AI](https://img.shields.io/badge/Jina-Embeddings-009C8F) ![FlashRank](https://img.shields.io/badge/FlashRank-0.2.10-FF6F61) ![BM25](https://img.shields.io/badge/BM25-Sparse_Retrieval-4B5563) |
| Model and observability | ![Portkey](https://img.shields.io/badge/Portkey-LLM_Gateway-6B4EFF) ![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-EE4C2C) ![Logfire](https://img.shields.io/badge/Pydantic_Logfire-4.3.1-ED9B17?logo=pydantic&logoColor=white) |
| Identity and data | ![Firebase](https://img.shields.io/badge/Firebase-11.10.0-DD2C00?logo=firebase&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-D71F00?logo=sqlalchemy&logoColor=white) ![Alembic](https://img.shields.io/badge/Alembic-1.16.4-2E6E9E) |
| Reminder delivery | ![Gmail](https://img.shields.io/badge/Gmail-SMTP_%2B_STARTTLS-EA4335?logo=gmail&logoColor=white) ![EasyCron](https://img.shields.io/badge/EasyCron-External_scheduler-2563EB) ![Cloudflare](https://img.shields.io/badge/Cloudflare_Tunnel-External_access-F38020?logo=cloudflare&logoColor=white) |
| Local infrastructure | ![Docker](https://img.shields.io/badge/Docker_Compose-PostgreSQL_%2B_Qdrant-2496ED?logo=docker&logoColor=white) |

## Repository layout

```text
backend/
├── agent/             # LangGraph workflow, Groq/Portkey client, guardrails, reranking
├── core/              # Configuration, Firebase authentication, Logfire setup
├── db/                # PostgreSQL schema, repository, Alembic migrations
├── retrieval/         # Qdrant hybrid retrieval and corpus ingestion
├── services/          # Gmail transport and independent reminder worker
├── tests/             # Unit tests and retrieval evaluation utilities
└── api.py             # FastAPI application

frontend/
└── src/               # React chat, auth, reminder, and API client UI
```

## Run locally

### 1. Prerequisites

- Python 3.11 or later
- Node.js 20 or later
- Docker Desktop
- A Firebase project and web application configuration
- Jina, Portkey, Groq, and Gmail SMTP credentials

### 2. Configure environment variables

Copy the examples and fill only the credentials you own:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Important backend values include Firebase Admin credentials, `JINA_API_KEY`, `PORTKEY_API_KEY`, `GROQ_API_KEY`, and the `SMTP_*` Gmail App Password settings. Never commit these values.

### 3. Start local data services and install dependencies

```bash
docker compose up -d

cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
alembic upgrade head

cd ../frontend
npm install
```

### 4. Index the medical corpus

```bash
cd backend
source .venv/bin/activate
python -m retrieval.ingest --batch-size 50
```

Use `--start <offset>` to resume a previously interrupted ingestion run.

### 5. Start the application

In one terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn api:app --reload
```

In another terminal:

```bash
cd frontend
npm run dev
```

## Email reminder scheduling

The reminder worker is independent of FastAPI scheduling and can still run as a CLI:

```bash
cd backend
source .venv/bin/activate
python -m services.reminder_worker
```

For EasyCron with Cloudflare Tunnel, configure a one-minute `POST` request to:

```text
https://<your-tunnel-host>/internal/reminders/run
```

Add this request header in EasyCron:

```text
X-Reminder-Worker-Token: <REMINDER_WORKER_TRIGGER_TOKEN>
```

Set the same long random value in `backend/.env`. The endpoint returns a delivery summary and is protected from unauthenticated invocation. Do not put this token in the URL.

## Quality checks

Run the backend tests:

```bash
cd backend
source .venv/bin/activate
pytest -q tests
```

Build the frontend:

```bash
cd frontend
npm run build
```

Run retrieval evaluation after indexing:

```bash
cd backend
source .venv/bin/activate
python tests/evaluation.py
```

## Security and safety notes

- Firebase ID tokens are verified server-side before user data is accessed.
- PostgreSQL is the source of truth for reminder schedules and delivery state.
- Every email occurrence is unique by `(reminder_id, scheduled_for)` and claimed with database row locking.
- SMTP credentials and scheduler trigger tokens are environment-only secrets.
- The retrieval pipeline uses guardrails and source-grounding, but output still requires clinical judgement.

## License

No license has been specified for this repository.
