"""Health & readiness endpoints."""
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("")
async def health():
    return {"status": "ok", "env": settings.env}


@router.get("/ready")
async def ready():
    return {"ready": True}
