"""FastAPI application entry point.

Run locally:  uv run uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import get_settings
from routers import admin_auth, chat, health, sessions
from services.guards import assert_crisis_script_approved

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tanya-iman")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    # Fail loudly at boot rather than quietly at the moment it matters most.
    assert_crisis_script_approved()

    if not settings.is_development and settings.answer_engine == "stub":
        raise RuntimeError(
            "REFUSING TO START: ANSWER_ENGINE=stub outside development. The stub "
            "returns a fixed answer regardless of the question."
        )

    logger.info(
        "starting env=%s engine=%s storage=%s llm=%s",
        settings.env,
        settings.answer_engine,
        settings.storage_backend,
        settings.llm_provider,
    )
    yield


app = FastAPI(
    title="Tanya Iman API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().is_development else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    """The widget is embedded in third-party WordPress sites (F-27), so
    `frame-ancestors` is an allowlist rather than DENY. It is empty by default;
    a site only gets to embed us once it is added to FRAME_ANCESTORS."""
    response = await call_next(request)
    settings = get_settings()

    ancestors = settings.frame_ancestor_list
    frame_policy = " ".join(ancestors) if ancestors else "'none'"
    response.headers["Content-Security-Policy"] = f"frame-ancestors {frame_policy}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Dual-mount routes: root for current frontend client, and /api for TDD §4 spec
app.include_router(health.router)
app.include_router(health.router, prefix="/api")

app.include_router(sessions.router)
app.include_router(sessions.router, prefix="/api")

app.include_router(chat.router)
app.include_router(chat.router, prefix="/api")

app.include_router(admin_auth.router, prefix="/admin/auth")
app.include_router(admin_auth.router, prefix="/api/admin/auth")
