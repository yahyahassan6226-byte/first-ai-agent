from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -----------------------------------------------------
    # APPLICATION
    # -----------------------------------------------------

    app_name: str = "First AI Agent API"
    app_version: str = "1.0.0"
    app_environment: str = "development"

    debug: bool = True

    # -----------------------------------------------------
    # API
    # -----------------------------------------------------

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    docs_enabled: bool = True

    # -----------------------------------------------------
    # CORS
    # -----------------------------------------------------

    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    cors_allow_credentials: bool = True

    # -----------------------------------------------------
    # HOST SECURITY
    # -----------------------------------------------------

    allowed_hosts: str = (
        "localhost,"
        "127.0.0.1"
    )

    force_https: bool = False

    # -----------------------------------------------------
    # REQUEST LIMITS
    # -----------------------------------------------------

    max_message_length: int = 10000

    # -----------------------------------------------------
    # OPENAI
    # -----------------------------------------------------

    openai_api_key: str | None = Field(
        default=None,
        repr=False,
    )

    model: str = "gpt-5-mini"

    # -----------------------------------------------------
    # WEATHER
    # -----------------------------------------------------

    openweather_api_key: str | None = Field(
        default=None,
        repr=False,
    )

    weather_api_key: str | None = Field(
        default=None,
        repr=False,
    )

    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------

    rag_chroma_dir: str = "rag_chroma_db"

    rag_collection_name: str = (
        "lesson24_documents"
    )

    embedding_model: str = (
        "text-embedding-3-small"
    )

    # -----------------------------------------------------
    # MEMORY
    # -----------------------------------------------------

    rag_agent_memory_db: str = (
        "rag_agent_memory.db"
    )

    # -----------------------------------------------------
    # LOGGING
    # -----------------------------------------------------

    log_level: str = "INFO"
    log_dir: str = "logs"

    # -----------------------------------------------------
    # HELPERS
    # -----------------------------------------------------

    def get_cors_origins(
        self,
    ) -> list[str]:

        return [
            item.strip()
            for item
            in self.cors_origins.split(",")
            if item.strip()
        ]

    def get_allowed_hosts(
        self,
    ) -> list[str]:

        return [
            item.strip()
            for item
            in self.allowed_hosts.split(",")
            if item.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()