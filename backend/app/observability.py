"""OpenTelemetry tracing for AgentForgeOps.

OTel is optional: if `opentelemetry-api`/`opentelemetry-sdk` aren't
installed, this module exposes no-op shims so the rest of the platform
keeps working (evals, agents, tests). When OTel is installed AND
`OTEL_EXPORTER_OTLP_ENDPOINT` is set, spans are exported via OTLP
(e.g. to the Jaeger all-in-one shipped in docker-compose).

Every LLM call gets a span with:
- llm.provider, llm.model
- llm.prompt_tokens, llm.completion_tokens
- llm.cost_usd
- duration (built into the span)
- exception + ERROR status on failures
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

_initialized = False

# USD per 1K tokens, (prompt, completion). Approximate published rates.
PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
    "claude-haiku-4-5": (0.0008, 0.004),
    "claude-sonnet-4-6": (0.003, 0.015),
    "claude-opus-4-6": (0.015, 0.075),
    "anthropic.claude-3-5-sonnet-20240620-v1:0": (0.003, 0.015),
    "anthropic.claude-3-haiku-20240307-v1:0": (0.00025, 0.00125),
}


def estimate_tokens(s: str) -> int:
    """Cheap fallback: ~4 chars per token."""
    return max(1, len(s) // 4)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rate = PRICING.get(model)
    if not rate:
        return 0.0
    p, c = rate
    return (prompt_tokens / 1000) * p + (completion_tokens / 1000) * c


# ---- OTel availability ---------------------------------------------------

try:  # pragma: no cover
    from opentelemetry import trace as _otel_trace
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    _otel_trace = None  # type: ignore[assignment]


class _NoopSpan:
    def set_attribute(self, *_a, **_kw) -> None: ...
    def record_exception(self, *_a, **_kw) -> None: ...
    def set_status(self, *_a, **_kw) -> None: ...
    def __enter__(self): return self
    def __exit__(self, *_a) -> None: ...


class _NoopTracer:
    @contextmanager
    def start_as_current_span(self, _name: str):
        yield _NoopSpan()


def init_tracing(service_name: str = "agentforgeops-backend") -> None:
    """Configure a global tracer. Idempotent. No-op when OTel isn't installed."""
    global _initialized
    if _initialized or not _OTEL_AVAILABLE:
        return

    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
            )
            logger.info("OTel exporter configured: %s", endpoint)
        except Exception as e:
            logger.warning("OTel exporter init failed, falling back to console: %s", e)
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif os.getenv("OTEL_CONSOLE", "").lower() in {"1", "true", "yes"}:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    _otel_trace.set_tracer_provider(provider)
    _initialized = True


def get_tracer():
    if not _OTEL_AVAILABLE:
        return _NoopTracer()
    return _otel_trace.get_tracer("agentforgeops")


def instrument_fastapi(app) -> None:
    """Auto-instrument an existing FastAPI app, if the package is available."""
    if not _OTEL_AVAILABLE:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass
