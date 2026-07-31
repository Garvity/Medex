from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://medassist:medassist_dev_password@localhost:5432/medassist"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "medical_knowledge"
    medical_dataset_path: str = "medical_rag_dataset.json"
    medical_dataset_url: str | None = "https://drive.google.com/uc?id=1JrCN_UG_4bJht6NbzQe3_a3ytqi3dXAG"
    firebase_project_id: str | None = None
    google_application_credentials: str | None = None
    jina_api_key: str | None = None
    jina_embedding_model: str = "jina-embeddings-v3"
    jina_embedding_dimensions: int = 1024
    portkey_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    # Portkey virtual keys. Each key should map to a separately configured Groq
    # credential in Portkey; the second target is used only when the first fails.
    portkey_primary_virtual_key: str = "@rag"
    portkey_fallback_virtual_key: str | None = "@brag"
    logfire_token: str | None = None
    logfire_service_name: str = "medassist-api"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_reply_to: str | None = None
    reminder_worker_batch_size: int = 50
    reminder_max_attempts: int = 5
    reminder_claim_timeout_minutes: int = 10
    reminder_worker_trigger_token: str | None = None
    nemo_guardrails_enabled: bool = True
    cors_allow_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
