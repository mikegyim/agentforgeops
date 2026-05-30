"""High-level retrieval entrypoint."""
from __future__ import annotations

from typing import List

from app.rag.embeddings import get_embedder
from app.rag.vector_store import VectorHit, get_vector_store


async def retrieve(query: str, top_k: int = 6) -> List[VectorHit]:
    embedder = get_embedder()
    vec = (await embedder.embed([query]))[0]
    store = get_vector_store()
    return await store.search(vec, top_k=top_k)
