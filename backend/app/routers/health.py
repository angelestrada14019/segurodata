"""GET /health — sin auth, sin rate limit (healthcheck de Railway)."""

from fastapi import APIRouter

from app import __version__
from app.config import get_settings
from app.limits import limiter

router = APIRouter(tags=["health"])


@router.get("/health")
@limiter.exempt
async def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "version": __version__, "env": settings.env}
