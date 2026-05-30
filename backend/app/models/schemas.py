"""Pydantic schemas for API IO."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: int
    name: str
    score: float
    snippet: str


class ChatRequest(BaseModel):
    message: str
    top_k: Optional[int] = 6


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 8


class SearchHit(BaseModel):
    source: str
    score: float
    text: str


class SearchResponse(BaseModel):
    hits: List[SearchHit]


class CodeReviewRequest(BaseModel):
    diff: str
    files: List[Dict[str, Any]] = Field(default_factory=list)
    repo: Optional[str] = None
    pr: Optional[int] = None


class TestGenerationRequest(BaseModel):
    code: str
    language: str = "python"
    framework: str = "pytest"


class DeployValidationRequest(BaseModel):
    manifests: List[Dict[str, str]]  # [{path, content}]


class IncidentTriageRequest(BaseModel):
    logs: str
    service: str = "unknown"
    time_window: str = "15m"


class DocsRequest(BaseModel):
    topic: str
    style: str = "markdown"


class OrchestrationRequest(BaseModel):
    workflow: List[Dict[str, Any]]
    input: Dict[str, Any] = Field(default_factory=dict)
