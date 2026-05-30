"""LLM client abstraction.

Providers: OpenAI, Anthropic, AWS Bedrock, and a deterministic mock.
All providers expose `generate()` returning text + token usage so the
TracedLLM wrapper can attach latency/tokens/cost to OTel spans.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import settings
from app.observability import (
    estimate_cost,
    estimate_tokens,
    get_tracer,
)


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLM:
    provider: str = "base"
    model: str = ""

    async def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
        r = await self.generate(prompt, max_tokens=max_tokens)
        return r.text

    async def generate(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        raise NotImplementedError


class MockLLM(LLM):
    provider = "mock"
    model = "mock-1"

    async def generate(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        head = prompt[:280].replace("\n", " ")
        text = (
            "## Summary\n"
            "Mock LLM response. Configure LLM_PROVIDER and the matching API key to use a real model.\n\n"
            f"## Echoed prompt head\n{head}\n"
        )
        return LLMResponse(
            text=text,
            prompt_tokens=estimate_tokens(prompt),
            completion_tokens=estimate_tokens(text),
        )


class OpenAIChat(LLM):
    provider = "openai"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
            )
            r.raise_for_status()
            data = r.json()
            usage = data.get("usage", {})
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                prompt_tokens=usage.get("prompt_tokens", 0) or estimate_tokens(prompt),
                completion_tokens=usage.get("completion_tokens", 0),
            )


class AnthropicChat(LLM):
    provider = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            data = r.json()
            parts = data.get("content", [])
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            usage = data.get("usage", {})
            return LLMResponse(
                text=text,
                prompt_tokens=usage.get("input_tokens", 0) or estimate_tokens(prompt),
                completion_tokens=usage.get("output_tokens", 0) or estimate_tokens(text),
            )


class BedrockChat(LLM):
    """AWS Bedrock client. Supports Anthropic-family models via the
    Messages API and Titan/Llama via inputText."""

    provider = "bedrock"

    def __init__(self, region: str, model: str):
        try:
            import boto3
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("boto3 is required for the Bedrock provider") from e
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model = model

    async def generate(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        anthropic_family = "anthropic" in self.model.lower() or "claude" in self.model.lower()
        if anthropic_family:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
        else:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {"maxTokenCount": max_tokens},
            }

        def _call():
            r = self.client.invoke_model(
                modelId=self.model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            return json.loads(r["body"].read())

        payload = await asyncio.to_thread(_call)

        if anthropic_family:
            parts = payload.get("content", [])
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            usage = payload.get("usage", {})
            return LLMResponse(
                text=text,
                prompt_tokens=usage.get("input_tokens", 0) or estimate_tokens(prompt),
                completion_tokens=usage.get("output_tokens", 0) or estimate_tokens(text),
            )
        text = payload.get("results", [{}])[0].get("outputText", "")
        return LLMResponse(
            text=text,
            prompt_tokens=estimate_tokens(prompt),
            completion_tokens=estimate_tokens(text),
        )


class TracedLLM(LLM):
    """Wraps any LLM with an OTel span around each call."""

    def __init__(self, inner: LLM):
        self.inner = inner
        self.provider = inner.provider
        self.model = inner.model

    async def generate(self, prompt: str, *, max_tokens: int = 1024) -> LLMResponse:
        tracer = get_tracer()
        with tracer.start_as_current_span("llm.generate") as span:
            span.set_attribute("llm.provider", self.provider)
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.prompt.length_chars", len(prompt))
            span.set_attribute("llm.max_tokens", max_tokens)
            try:
                resp = await self.inner.generate(prompt, max_tokens=max_tokens)
            except Exception as exc:
                span.record_exception(exc)
                span.set_attribute("llm.error", True)
                raise
            span.set_attribute("llm.prompt_tokens", resp.prompt_tokens)
            span.set_attribute("llm.completion_tokens", resp.completion_tokens)
            span.set_attribute(
                "llm.cost_usd",
                estimate_cost(self.model, resp.prompt_tokens, resp.completion_tokens),
            )
            return resp


_llm: Optional[LLM] = None


def get_llm() -> LLM:
    global _llm
    if _llm is not None:
        return _llm

    p = settings.llm_provider
    try:
        if p == "openai" and settings.openai_api_key:
            inner: LLM = OpenAIChat(settings.openai_api_key, settings.llm_model)
        elif p == "anthropic" and settings.anthropic_api_key:
            inner = AnthropicChat(settings.anthropic_api_key, settings.llm_model)
        elif p == "bedrock":
            inner = BedrockChat(settings.aws_region, settings.bedrock_model or settings.llm_model)
        else:
            inner = MockLLM()
    except Exception:
        inner = MockLLM()

    _llm = TracedLLM(inner)
    return _llm
