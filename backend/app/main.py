"""
AgentForgeOps backend entrypoint.

Boots FastAPI, wires routers, exposes /health, initializes OTel tracing.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, chat, health, rag, upload, webhooks
from app.config import settings
from app.models.db import init_db
from app.observability import init_tracing, instrument_fastapi
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AgentForgeOps backend (env=%s)", settings.env)
    init_tracing()
    await init_db()
    get_vector_store()
    yield
    logger.info("Shutting down AgentForgeOps backend")


app = FastAPI(
    title="AgentForgeOps API",
    description="AI-Native DevOps & Software Engineering Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

instrument_fastapi(app)


@app.get("/")
async def root():
    return {
        "service": "AgentForgeOps",
        "version": "0.1.0",
        "docs": "/docs",
    }
