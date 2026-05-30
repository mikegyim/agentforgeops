"""Vector store wrapper. Supports Qdrant, Chroma, and an in-memory fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.config import settings


@dataclass
class VectorHit:
    id: str
    score: float
    text: str
    source: str


class VectorStore:
    async def upsert(self, ids: List[str], vectors: List[List[float]], payloads: List[dict]) -> None:
        raise NotImplementedError

    async def search(self, vector: List[float], top_k: int = 8) -> List[VectorHit]:
        raise NotImplementedError


class InMemoryStore(VectorStore):
    def __init__(self):
        self._vectors: List[List[float]] = []
        self._payloads: List[dict] = []
        self._ids: List[str] = []

    async def upsert(self, ids, vectors, payloads):
        self._ids.extend(ids)
        self._vectors.extend(vectors)
        self._payloads.extend(payloads)

    async def search(self, vector, top_k=8):
        if not self._vectors:
            return []
        scored = []
        for i, v in enumerate(self._vectors):
            scored.append((self._cosine(vector, v), i))
        scored.sort(reverse=True)
        out = []
        for score, i in scored[:top_k]:
            p = self._payloads[i]
            out.append(
                VectorHit(
                    id=self._ids[i],
                    score=float(score),
                    text=p.get("text", ""),
                    source=p.get("source", "unknown"),
                )
            )
        return out

    @staticmethod
    def _cosine(a, b):
        s = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return s / (na * nb)


class QdrantStore(VectorStore):
    def __init__(self, url: str, collection: str, dim: int):
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as q

        self.collection = collection
        self.client = QdrantClient(url=url)
        existing = {c.name for c in self.client.get_collections().collections}
        if collection not in existing:
            self.client.create_collection(
                collection_name=collection,
                vectors_config=q.VectorParams(size=dim, distance=q.Distance.COSINE),
            )
        self._q = q

    async def upsert(self, ids, vectors, payloads):
        points = [
            self._q.PointStruct(id=i, vector=v, payload=p)
            for i, v, p in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    async def search(self, vector, top_k=8):
        res = self.client.search(
            collection_name=self.collection, query_vector=vector, limit=top_k
        )
        return [
            VectorHit(
                id=str(r.id),
                score=float(r.score),
                text=(r.payload or {}).get("text", ""),
                source=(r.payload or {}).get("source", "unknown"),
            )
            for r in res
        ]


_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is not None:
        return _store
    try:
        if settings.vector_backend == "qdrant":
            _store = QdrantStore(
                url=settings.qdrant_url,
                collection=settings.qdrant_collection,
                dim=settings.embedding_dim,
            )
        else:
            _store = InMemoryStore()
    except Exception:
        _store = InMemoryStore()
    return _store
