"""Documentation Agent — drafts/updates docs grounded in indexed context."""
from __future__ import annotations

from typing import Any, Dict

from app.agents.base import Agent
from app.integrations.llm import get_llm
from app.rag.retriever import retrieve


class DocsAgent(Agent):
    name = "Documentation Agent"
    description = "Drafts and updates engineering docs grounded in indexed context."

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic: str = payload.get("topic", "")
        style: str = payload.get("style", "markdown")
        hits = await retrieve(topic, top_k=8)
        ctx = "\n\n".join(f"[{i+1}] ({h.source}) {h.text}" for i, h in enumerate(hits))

        llm = get_llm()
        draft = await llm.complete(
            f"Draft an engineering document on `{topic}` in {style} format. "
            f"Use only the context provided and cite sources as [#1], [#2], etc.\n\n"
            f"# Context\n{ctx}\n"
        )
        return {
            "agent": self.name,
            "topic": topic,
            "draft": draft,
            "sources": [h.source for h in hits],
        }
