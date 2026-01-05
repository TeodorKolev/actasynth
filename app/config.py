"""Application configuration using Pydantic Settings"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Keys
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(..., validation_alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(..., validation_alias="GOOGLE_API_KEY")

    # LangSmith
    langchain_tracing_v2: bool = Field(default=True, validation_alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(None, validation_alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(
        default="agentops-studio", validation_alias="LANGCHAIN_PROJECT"
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/agentops",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # Storage
    s3_bucket: str = Field(default="agentops-artifacts", validation_alias="S3_BUCKET")
    s3_endpoint: Optional[str] = Field(None, validation_alias="S3_ENDPOINT")
    s3_access_key: Optional[str] = Field(None, validation_alias="S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = Field(None, validation_alias="S3_SECRET_KEY")

    # Observability
    sentry_dsn: Optional[str] = Field(None, validation_alias="SENTRY_DSN")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Service
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    workers: int = Field(default=4, validation_alias="WORKERS")
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")

    def get_api_keys(self) -> dict[str, str]:
        """Get all API keys as a dictionary"""
        return {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
        }


# Singleton instance
settings = Settings()
