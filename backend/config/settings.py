"""Runtime configuration.

A single ``ENV`` variable drives behaviour; everything else is derived from or
gated on it. See docs/tdd.md section 5.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Env = Env.development
    gcloud_project: str = "tanya-iman-local"

    # Development only. Must be ABSENT on Cloud Run — an empty string makes the
    # Firestore SDK dial an empty gRPC URI and crash at startup.
    firestore_emulator_host: str | None = None
    storage_backend: str = "memory"
    firestore_database: str = "(default)"

    answer_engine: str = "stub"
    prompt_version: str = "0.1.0-stub"

    llm_provider: str = "fake"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-latest"
    llm_fallback_provider: str = "fake"
    llm_fallback_model: str = "gemini-2.0-flash"
    embedding_model: str = "text-multilingual-embedding-002"

    otp_provider: str = "fake"
    otp_api_key: str = ""
    otp_service_sid: str = ""
    firebase_service_account: str = ""
    auth_allow_insecure_dev_tokens: bool = True

    admin_jwt_secret: str = "change-me-in-every-environment"
    phone_encryption_key: str = ""

    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    frame_ancestors: str = ""

    # Defaults mirror the seeded `system_config` documents (TDD section 3.9).
    rate_limit_per_hour: int = Field(default=30, ge=1)
    otp_requests_per_hour: int = Field(default=5, ge=1)
    max_question_chars: int = Field(default=1000, ge=1)
    session_ttl_hours: int = Field(default=24, ge=1)
    context_turns: int = Field(default=3, ge=0)
    retention_months: int = Field(default=12, ge=1)
    similarity_threshold: float = Field(default=0.72, ge=0.0, le=1.0)

    @field_validator("firestore_emulator_host", mode="before")
    @classmethod
    def _blank_host_is_none(cls, value: object) -> object:
        # Treat "" as unset. Anything else here becomes a startup crash that is
        # very hard to read from a Cloud Run log.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def is_development(self) -> bool:
        return self.env is Env.development

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def frame_ancestor_list(self) -> list[str]:
        return [o.strip() for o in self.frame_ancestors.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
