"""Application configuration module using Pydantic Settings."""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Tiv AI Data Collection Platform backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Runtime
    ENVIRONMENT: str = Field(default="development", description="Runtime environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug logging and auto-reload")
    HOST: str = Field(default="0.0.0.0", description="Bind host")
    PORT: int = Field(default=8000, description="Bind port")

    # CORS (Developer 2 Frontend Integration)
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed origins for CORS requests",
    )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database Configuration (Developer 1)
    # Default to local SQLite for frictionless zero-dependency development/testing;
    # overridden by DATABASE_URL in .env for PostgreSQL.
    DATABASE_URL: str = Field(
        default="sqlite:///./tiv_ai_dev.db",
        description="SQLAlchemy database connection URL",
    )

    # Storage Abstraction Settings (Developer 3)
    STORAGE_BACKEND: str = Field(default="local", description="Storage provider: 'local' or 's3'")
    LOCAL_STORAGE_PATH: str = Field(default=".storage", description="Root path for local filesystem storage")

    # Cloud Storage (S3 / R2 - when STORAGE_BACKEND=s3)
    S3_BUCKET_NAME: str = Field(default="tiv-ai-data-private", description="S3 bucket name")
    S3_REGION: str = Field(default="us-east-1", description="S3 region")
    S3_ENDPOINT_URL: Union[str, None] = Field(default=None, description="Custom S3 endpoint for MinIO/R2")
    S3_ACCESS_KEY_ID: Union[str, None] = Field(default=None, description="S3 access key")
    S3_SECRET_ACCESS_KEY: Union[str, None] = Field(default=None, description="S3 secret key")
    S3_PRESIGNED_EXPIRATION_SECONDS: int = Field(default=900, description="Presigned URL TTL in seconds (15 min)")

    # Ingestion Constraints & Validation Rules
    MAX_AUDIO_SIZE_BYTES: int = Field(default=26214400, description="Maximum audio file size (25 MB)")
    MIN_AUDIO_DURATION_SECONDS: float = Field(default=0.5, description="Minimum allowed audio duration in seconds")
    MAX_AUDIO_DURATION_SECONDS: float = Field(default=120.0, description="Maximum allowed audio duration in seconds")
    CONSENT_VERSION: str = Field(default="v1.0-2026-09", description="Active legal consent version")


settings = Settings()
