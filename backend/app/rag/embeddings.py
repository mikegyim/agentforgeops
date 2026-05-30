"""Embedding providers. Falls back to a deterministic hash-based encoder
so the stack runs end-to-end without external API keys."""
from __future__ import annotations

import hashlib
from typing import List

from app.config import settings


class Embedder:
    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class HashEmbedder(Embedder):
    """Deterministic fallback. Not for production — for local dev only."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    async def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # Expand the 32-byte hash to `dim` floats in [-1, 1].
            buf = (h * ((self.dim // len(h)) + 1))[: self.dim]
            vec = [(b / 127.5) - 1.0 for b in buf]
            out.append(vec)
        return out


class LocalSentenceTransformer(Embedder):
    """Uses sentence-transformers if installed, else falls back to HashEmbedder."""

    def __init__(self, model: str):
        self.model_name = model
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:  # pragma: no cover
                self._model = HashEmbedder(settings.embedding_dim)
        return self._model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        m = self._load()
        if isinstance(m, HashEmbedder):
            return await m.embed(texts)
        vecs = m.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vecs]


def get_embedder() -> Embedder:
    if settings.embedding_provider == "local":
        return LocalSentenceTransformer(settings.embedding_model)
    return HashEmbedder(settings.embedding_dim)
