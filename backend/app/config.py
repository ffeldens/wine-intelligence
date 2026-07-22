"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database (Postgres + pgvector)
    database_url: str = "postgresql://wine:password@localhost:5432/wine_intelligence"

    # AI APIs (mesmo padrão do salesclub-intel: Claude primário + OpenAI fallback)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ai_primary_provider: str = "anthropic"
    ai_model_anthropic: str = "claude-sonnet-5"
    # Modelo barato p/ enriquecimento em lote (perfil sensorial de cada vinho)
    ai_model_anthropic_cheap: str = "claude-haiku-4-5-20251001"
    ai_model_openai: str = "gpt-4o"

    # Embeddings (Anthropic não tem API de embeddings → OpenAI)
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # App
    app_name: str = "Wine Intelligence — Sommelier IA (TDP Wines)"
    app_url: str = "http://localhost:8000"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
