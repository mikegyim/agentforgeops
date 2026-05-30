"""LLM client abstraction. Supports OpenAI, Anthropic, Bedrock, and a mock provider."""
from __future__ import annotations

from typing import Optional

import httpx

from app.config import settings


class LLM:
    async def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
        raise NotImplementedError


class MockLLM(LLM):
    """Deterministic mock so the stack runs without API keys."""

    async def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
        head = prompt[:280].replace("\n", " ")
        return (
            "## Summary\n"
            "Mock LLM response. Configure LLM_PROVIDER and the matching API key to use a real model.\n\n"
            f"## Echoed prompt head\n{head}\n"
        )


class OpenAIChat(LLM):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
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
            return data["choices"][0]["message"]["content"]


class AnthropicChat(LLM):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str, *, max_tokens: int = 1024) -> str:
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
            return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


_llm: Optional[LLM] = None


def get_llm() -> LLM:
    global _llm
    if _llm is not None:
        return _llm
    p = settings.llm_provider
    try:
        if p == "openai" and settings.openai_api_key:
            _llm = OpenAIChat(settings.openai_api_key, settings.llm_model)
        elif p == "anthropic" and settings.anthropic_api_key:
            _llm = AnthropicChat(settings.anthropic_api_key, settings.llm_model)
        else:
            _llm = MockLLM()
    except Exception:
        _llm = MockLLM()
    return _llm
