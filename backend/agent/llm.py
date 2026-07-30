from langchain_openai import ChatOpenAI

from core.config import get_settings


def get_llm() -> ChatOpenAI:
    settings = get_settings()
    if not settings.portkey_api_key or not settings.groq_api_key:
        raise RuntimeError("PORTKEY_API_KEY and GROQ_API_KEY must be configured before answer generation can run.")
    return ChatOpenAI(
        model=settings.groq_model,
        api_key=settings.portkey_api_key,
        base_url="https://api.portkey.ai/v1",
        default_headers={
            "x-portkey-provider": "@rag",
            #"x-portkey-provider-api-key": settings.groq_api_key,
        },
        temperature=0.1,
        timeout=45,
    )
