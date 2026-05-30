"""OpenTelemetry tracing for AgentForgeOps.

Spans are exported via OTLP if `OTEL_EXPORTER_OTLP_ENDPOINT` is set
(the docker-compose stack ships a Jaeger all-in-one on :4317).
Otherwise this is a no-op and the app runs normally.

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
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

_initialized = False

# USD per 1K tokens, (prompt, completion). Approximate published rates;
# real billing is whatever Anthropic/OpenAI/AWS charge you.
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
    """Very rough fallback: ~4 chars per token."""
    return max(1, len(s) // 4)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rate = PRICING.get(model)
    if not rate:
        return 0.0
    p, c = rate
    return (prompt_tokens / 1000) * p + (completion_tokens / 1000) * c


def init_tracing(service_name: str = "agentforgeops-backend") -> None:
    """Configure a global tracer. Idempotent."""
    global _initialized
    if _initialized:
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
        except Exception as e:  # pragma: no cover
            logger.warning("OTel exporter init failed, falling back to console: %s", e)
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif os.getenv("OTEL_CONSOLE", "").lower() in {"1", "true", "yes"}:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI HTTP server (best-effort).
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa
    except Exception:  # pragma: no cover
        pass

    _initialized = True


def get_tracer():
    return trace.get_tracer("agentforgeops")


def instrument_fastapi(app) -> None:
    """Auto-instrument an existing FastAPI app, if the package is available."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception:  # pragma: no cover
        pass
