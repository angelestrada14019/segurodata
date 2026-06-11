"""GET /whoami — pre-mortem T5: detecta comandante sin cuadrante asignado."""

from fastapi import APIRouter, Request

from app.dependencies import CurrentUser
from app.schemas.auth import WhoAmIResponse

router = APIRouter(tags=["auth"])


@router.get("/whoami", response_model=WhoAmIResponse)
async def whoami(request: Request, user: CurrentUser) -> dict:
    return {
        "rol": user.rol,
        "cuadrante_asignado": user.cuadrante_asignado,
        "cuadrante_pendiente": user.cuadrante_pendiente,
    }
