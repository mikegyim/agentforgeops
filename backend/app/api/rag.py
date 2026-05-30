"""RAG search endpoint."""
from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse, SearchHit
from app.rag.retriever import retrieve

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    hits = await retrieve(req.query, top_k=req.top_k or 8)
    return SearchResponse(
        hits=[
            SearchHit(source=h.source, score=h.score, text=h.text)
            for h in hits
        ]
    )
