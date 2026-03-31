"""Application configuration using Pydantic Settings"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Keys (Optional — at least one must be set at runtime)
    openai_api_key: Optional[str] = Field(None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, validation_alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(None, validation_alias="GOOGLE_API_KEY")

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

    # Cognito Auth
    cognito_region: Optional[str] = Field(None, validation_alias="COGNITO_REGION")
    cognito_user_pool_id: Optional[str] = Field(None, validation_alias="COGNITO_USER_POOL_ID")
    cognito_client_id: Optional[str] = Field(None, validation_alias="COGNITO_CLIENT_ID")

    # Observability
    sentry_dsn: Optional[str] = Field(None, validation_alias="SENTRY_DSN")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # CORS
    allowed_origins: list[str] = Field(default=["*"], validation_alias="ALLOWED_ORIGINS")

    # Service
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    workers: int = Field(default=4, validation_alias="WORKERS")
    log_level: str = Field(default="info", validation_alias="LOG_LEVEL")

    def get_api_keys(self) -> dict[str, str]:
        """Get configured API keys as a dictionary (only non-None keys included)"""
        keys = {}
        if self.openai_api_key:
            keys["openai"] = self.openai_api_key
        if self.anthropic_api_key:
            keys["anthropic"] = self.anthropic_api_key
        if self.google_api_key:
            keys["google"] = self.google_api_key
        return keys


# Singleton instance
settings = Settings()
