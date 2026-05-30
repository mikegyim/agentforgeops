"""RAG smoke tests."""
import asyncio

from app.rag.indexer import chunk
from app.rag.retriever import retrieve
from app.rag.embeddings import HashEmbedder
from app.rag.vector_store import InMemoryStore


def test_chunk_splits_text():
    text = "a" * 2500
    out = chunk(text, size=1000, overlap=100)
    assert len(out) >= 3
    assert all(len(c) <= 1000 for c in out)


def test_inmemory_round_trip():
    async def go():
        store = InMemoryStore()
        emb = HashEmbedder(dim=32)
        vecs = await emb.embed(["kubernetes pod crash", "billing pipeline retries"])
        await store.upsert(
            ids=["a", "b"],
            vectors=vecs,
            payloads=[
                {"text": "kubernetes pod crash", "source": "runbook-1"},
                {"text": "billing pipeline retries", "source": "runbook-2"},
            ],
        )
        q = (await emb.embed(["pod crash"]))[0]
        hits = await store.search(q, top_k=2)
        assert hits and hits[0].source in {"runbook-1", "runbook-2"}

    asyncio.run(go())
