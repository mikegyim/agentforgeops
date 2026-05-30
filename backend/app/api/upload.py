"""Upload + index endpoints for docs, code, runbooks."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.rag.indexer import index_file

router = APIRouter()


@router.post("")
async def upload(files: List[UploadFile] = File(...)):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    results = []
    for f in files:
        if f.size and f.size > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"{f.filename} too large")

        doc_id = uuid.uuid4().hex
        ext = os.path.splitext(f.filename or "")[1].lower() or ".bin"
        dest = Path(settings.upload_dir) / f"{doc_id}{ext}"
        contents = await f.read()
        dest.write_bytes(contents)

        chunks = await index_file(str(dest), source_name=f.filename or doc_id)
        results.append(
            {
                "filename": f.filename,
                "doc_id": doc_id,
                "chunks": chunks,
                "path": str(dest),
            }
        )
    return {"indexed": results}
