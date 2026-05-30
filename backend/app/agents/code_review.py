"""Code Review Agent — reviews a diff or set of changed files."""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import Agent
from app.integrations.llm import get_llm
from app.rag.retriever import retrieve

PROMPT = """You are a senior staff engineer performing a code review.
Review the diff below. Look for:
- Correctness bugs and logic errors
- Security issues (auth, injection, secrets, supply chain)
- Performance concerns
- Test coverage gaps
- Style/maintainability

Use the team context (architecture docs, conventions) to ground your feedback.

# Team context
{context}

# Diff
{diff}

Return a structured review:
## Summary
## Risk: low | medium | high
## Findings (numbered)
## Suggested tests
"""


class CodeReviewAgent(Agent):
    name = "Code Review Agent"
    description = "Reviews PR diffs grounded in team conventions, flags risk."

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        diff: str = payload.get("diff", "")
        files: List[Dict[str, Any]] = payload.get("files", [])

        # Retrieve grounding context based on the file paths and diff.
        query = "code review " + " ".join(f.get("filename", "") for f in files)[:512]
        hits = await retrieve(query, top_k=5)
        context = "\n\n".join(f"- ({h.source}) {h.text[:400]}" for h in hits)

        llm = get_llm()
        review = await llm.complete(PROMPT.format(context=context or "(none)", diff=diff[:12_000]))

        # Heuristic risk extraction.
        risk = "medium"
        lower = review.lower()
        if "risk: high" in lower or "critical" in lower:
            risk = "high"
        elif "risk: low" in lower:
            risk = "low"

        return {
            "agent": self.name,
            "risk": risk,
            "summary": review,
            "sources": [h.source for h in hits],
            "file_count": len(files),
        }
