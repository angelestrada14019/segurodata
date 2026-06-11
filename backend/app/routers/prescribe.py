"""POST /prescribe — recomendación operacional (solo COMANDANTE/ANALISTA/ADMIN)."""

from fastapi import APIRouter, Depends, Request

from app.core.security import UserClaims
from app.dependencies import get_prescribe_service, require_roles
from app.limits import limite_llm, limiter
from app.schemas.prescribe import PrescribeRequest, PrescribeResponse
from app.services.prescribe_service import PrescribeService

router = APIRouter(tags=["prescriptivo"])


@router.post("/prescribe", response_model=PrescribeResponse, response_model_exclude_none=True)
@limiter.limit(limite_llm)
async def prescribe(
    request: Request,
    body: PrescribeRequest,
    user: UserClaims = require_roles("COMANDANTE_CAI", "ANALISTA_SDSCJ", "ADMIN"),
    service: PrescribeService = Depends(get_prescribe_service),
) -> dict:
    shap_top = [item.model_dump() for item in body.shap_top]
    return await service.prescribe(user, body.upz_cod, shap_top)
