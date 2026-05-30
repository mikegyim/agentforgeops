"""Chunk-and-embed pipeline for uploaded files."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from app.rag.embeddings import get_embedder
from app.rag.vector_store import get_vector_store

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
SUPPORTED_TEXT = {".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".yaml", ".yml",
                  ".tf", ".json", ".toml", ".cfg", ".ini", ".html", ".css", ".sh", ".log"}


def _read_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() in SUPPORTED_TEXT:
        return p.read_text(encoding="utf-8", errors="ignore")
    # Best-effort: try utf-8.
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    if not text:
        return []
    out: List[str] = []
    i = 0
    while i < len(text):
        out.append(text[i : i + size])
        i += size - overlap
    return out


async def index_file(path: str, source_name: str) -> int:
    text = _read_text(path)
    pieces = chunk(text)
    if not pieces:
        return 0
    embedder = get_embedder()
    vecs = await embedder.embed(pieces)
    store = get_vector_store()
    ids = [uuid.uuid4().hex for _ in pieces]
    payloads = [{"text": p, "source": source_name, "path": path} for p in pieces]
    await store.upsert(ids=ids, vectors=vecs, payloads=payloads)
    return len(pieces)


async def index_directory(root: str) -> int:
    total = 0
    for dp, _, files in os.walk(root):
        for fn in files:
            full = os.path.join(dp, fn)
            try:
                total += await index_file(full, source_name=os.path.relpath(full, root))
            except Exception:
                continue
    return total
