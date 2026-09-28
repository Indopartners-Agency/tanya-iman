from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import (
    AdminRole,
    AnswerSource,
    ArticleStatus,
    AuthMethod,
    ChunkDecision,
    Platform,
    ValidatorCode,
)

# --- Stored entities ---------------------------------------------------------


class User(BaseModel):
    uid: str
    auth_method: AuthMethod
    phone_e164_enc: str | None = None
    phone_hash: str | None = None
    created_at: datetime
    last_active_at: datetime
    superseded_by: str | None = None
    question_count: int = 0


class Session(BaseModel):
    id: str
    uid: str
    platform: Platform = Platform.web
    embed_origin: str | None = None
    started_at: datetime
    last_message_at: datetime
    expires_at: datetime
    message_count: int = 0


class Citation(BaseModel):
    title: str
    url: str
    site: str
    article_id: str | None = None


class Question(BaseModel):
    id: str
    session_id: str
    uid: str
    question_text: str
    answer_text: str | None = None
    answer_source: AnswerSource
    topic_slug: str | None = None
    cluster_id: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    like_count: int = 0
    is_refused: bool = False
    is_crisis: bool = False
    has_grounding: bool = False
    validator_failures: list[ValidatorCode] = Field(default_factory=list)
    model: str | None = None
    prompt_version: str | None = None
    latency_ms: int = 0
    created_at: datetime


class Topic(BaseModel):
    slug: str
    name_id: str
    name_en: str
    curated_answer: str | None = None
    curated_citations: list[Citation] = Field(default_factory=list)
    curated_status: str = "draft"
    updated_by: str | None = None
    updated_at: datetime | None = None
    question_count: int = 0
    like_count: int = 0


class SystemConfig(BaseModel):
    key: str
    value: str
    updated_by: str | None = None
    updated_at: datetime | None = None


class Article(BaseModel):
    id: str
    site: str
    url: str
    title: str
    published_at: datetime | None = None
    summary: str = ""
    cleaned_text: str | None = None
    topic_slugs: list[str] = Field(default_factory=list)
    content_hash: str
    first_seen_at: datetime
    last_crawled_at: datetime
    status: ArticleStatus = ArticleStatus.active


class ArticleChunk(BaseModel):
    id: str  # {article_id}#{chunk_index}
    article_id: str
    site: str
    url: str
    title: str
    chunk_index: int
    text: str
    embedding: list[float] | None = None
    embedding_model: str = "text-multilingual-embedding-002"
    token_count: int = 0
    has_forbidden_term: bool = False
    is_retrievable: bool = True
    created_at: datetime


class FlaggedChunk(BaseModel):
    id: str
    chunk_id: str
    article_id: str
    site: str
    url: str
    title: str
    matched_terms: list[str] = Field(default_factory=list)
    text: str
    decision: ChunkDecision = ChunkDecision.pending
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None


# --- Engine contract ---------------------------------------------------------


class EngineResult(BaseModel):
    """What any answer engine returns. The stub and the real pipeline both
    satisfy this, so Phase 5 swaps the engine without touching the router."""

    answer_source: AnswerSource
    answer_text: str
    citations: list[Citation] = Field(default_factory=list)
    topic_slug: str | None = None
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    validator_failures: list[ValidatorCode] = Field(default_factory=list)
    model: str | None = None
    prompt_version: str | None = None


# --- API surface -------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    platform: Platform = Platform.web
    embed_origin: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str


class AskRequest(BaseModel):
    session_id: str
    text: str


class AskResponse(BaseModel):
    question_id: str
    answer_source: AnswerSource
    answer_text: str
    citations: list[Citation] = Field(default_factory=list)
    topic_slug: str | None = None
    likeable: bool
    latency_ms: int


class LikeResponse(BaseModel):
    question_id: str
    liked: bool
    like_count: int


class HealthResponse(BaseModel):
    status: str
    env: str
    prompt_version: str
    corpus_chunk_count: int
    # Surfaced so that "staging is still running the stub" is visible in a
    # smoke check rather than discovered by a seeker.
    engine: str


# --- Admin entities ----------------------------------------------------------


class AdminUser(BaseModel):
    id: str
    email: str
    password_hash: str
    role: AdminRole
    refresh_token_hash: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class AdminAuditLog(BaseModel):
    id: str
    admin_id: str
    action: str
    target_id: str
    detail: str
    created_at: datetime


# --- Auth API models ---------------------------------------------------------


class OTPRequestPayload(BaseModel):
    channel: str = Field(..., pattern="^(sms|whatsapp)$")
    phone: str


class OTPRequestResponse(BaseModel):
    status: str = "ok"
    message: str | None = None


class OTPVerifyPayload(BaseModel):
    phone: str
    code: str


class OTPVerifyResponse(BaseModel):
    custom_token: str
    is_new_user: bool = False


class ConvertPayload(BaseModel):
    anonymous_uid: str


class ConvertResponse(BaseModel):
    status: str = "ok"
    sessions_transferred: int
    questions_transferred: int
    likes_transferred: int


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: AdminRole
    email: str


class AdminRefreshRequest(BaseModel):
    refresh_token: str


class AdminRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminBootstrapRequest(BaseModel):
    email: str
    password: str


class AdminBootstrapResponse(BaseModel):
    status: str = "ok"
    admin_id: str
