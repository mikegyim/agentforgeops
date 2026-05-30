"""Grounded chat endpoint backed by RAG."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, Source
from app.rag.retriever import retrieve
from app.integrations.llm import get_llm

router = APIRouter()


SYSTEM_PROMPT = (
    "You are AgentForgeOps, an AI engineering co-pilot. "
    "Answer the user's question using ONLY the provided context. "
    "If the context is insufficient, say so. Cite source ids inline as [#1], [#2]."
)


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    hits = await retrieve(req.message, top_k=req.top_k or 6)
    context_block = "\n\n".join(
        f"[#{i+1}] ({h.source}) {h.text}" for i, h in enumerate(hits)
    )
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"# Context\n{context_block}\n\n"
        f"# Question\n{req.message}"
    )

    llm = get_llm()
    answer = await llm.complete(prompt)

    return ChatResponse(
        answer=answer,
        sources=[
            Source(id=i + 1, name=h.source, score=h.score, snippet=h.text[:240])
            for i, h in enumerate(hits)
        ],
    )
